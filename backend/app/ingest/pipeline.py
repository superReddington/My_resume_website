from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.db.pool import get_pool
from app.ingest.chunking import split_pages
from app.ingest.embeddings import embed_texts, embeddings_enabled
from app.ingest.pdf import extract_pages

logger = logging.getLogger(__name__)

BATCH_SIZE = 32


def ingest_pdf(
    filename: str,
    pdf_bytes: bytes,
    *,
    replace_existing: bool = False,
) -> dict:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("只支持 PDF 文件")
    if len(pdf_bytes) > settings.max_upload_mb * 1024 * 1024:
        raise ValueError(f"文件不能超过 {settings.max_upload_mb}MB")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}.pdf"
    storage_path = settings.upload_dir / stored_name
    storage_path.write_bytes(pdf_bytes)

    pool = get_pool()
    with pool.connection() as conn:
        if replace_existing:
            _delete_all_documents(conn)

        row = conn.execute(
            """
            INSERT INTO documents (filename, storage_path, byte_size, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id, filename, byte_size, status, created_at
            """,
            (filename, str(storage_path), len(pdf_bytes)),
        ).fetchone()
        if row is None:
            raise RuntimeError("写入文档记录失败")
        document_id = row[0]

        try:
            pages = extract_pages(pdf_bytes)
            if not pages:
                raise ValueError("未能从 PDF 提取文字，可能是扫描件，请上传可选中文字的简历")

            page_pairs = [(page.number, page.text) for page in pages]
            chunks = split_pages(
                page_pairs,
                settings.chunk_size,
                settings.chunk_overlap,
            )
            if not chunks:
                raise ValueError("PDF 解析后没有可用文本块")

            if embeddings_enabled():
                embeddings = _embed_in_batches([content for _, content in chunks])
            else:
                embeddings = [None] * len(chunks)
            for index, ((page_number, content), embedding) in enumerate(
                zip(chunks, embeddings, strict=True)
            ):
                conn.execute(
                    """
                    INSERT INTO chunks (
                        document_id, chunk_index, page_number, content, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (document_id, index, page_number, content, embedding),
                )

            conn.execute(
                """
                UPDATE documents
                SET page_count = %s,
                    chunk_count = %s,
                    status = 'embedded',
                    error = NULL,
                    updated_at = now()
                WHERE id = %s
                """,
                (len(pages), len(chunks), document_id),
            )
        except Exception as exc:
            conn.execute(
                """
                UPDATE documents
                SET status = 'failed', error = %s, updated_at = now()
                WHERE id = %s
                """,
                (str(exc), document_id),
            )
            raise

        return get_document(str(document_id)) or {}


def list_documents() -> list[dict]:
    pool = get_pool()
    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, byte_size, page_count, chunk_count, status, error, created_at
            FROM documents
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [_document_row(row) for row in rows]


def get_document(document_id: str) -> dict | None:
    pool = get_pool()
    with pool.connection() as conn:
        row = conn.execute(
            """
            SELECT id, filename, byte_size, page_count, chunk_count, status, error, created_at
            FROM documents
            WHERE id = %s
            """,
            (document_id,),
        ).fetchone()
    return _document_row(row) if row else None


def list_chunks(document_id: str) -> list[dict]:
    pool = get_pool()
    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT id, chunk_index, page_number, content
            FROM chunks
            WHERE document_id = %s
            ORDER BY chunk_index
            """,
            (document_id,),
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "chunk_index": row[1],
            "page_number": row[2],
            "content": row[3],
        }
        for row in rows
    ]


def delete_document(document_id: str) -> bool:
    pool = get_pool()
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT storage_path FROM documents WHERE id = %s",
            (document_id,),
        ).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))
    path = Path(row[0])
    if path.exists():
        path.unlink()
    return True


def search_chunks(query: str, limit: int = 8) -> list[dict]:
    query = query.strip()
    if not query:
        return []

    pool = get_pool()
    with pool.connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        if not total or total[0] == 0:
            return []
        chunk_count = int(total[0])
        fetch_limit = chunk_count if chunk_count <= 16 else limit

        vector_rows: list[tuple] = []
        if embeddings_enabled():
            try:
                embedding = embed_texts([query])[0]
                vector_rows = conn.execute(
                    """
                    SELECT c.id, c.content, c.page_number, c.chunk_index, d.filename,
                           1 - (c.embedding <=> %s::vector) AS score
                    FROM chunks c
                    JOIN documents d ON d.id = c.document_id
                    WHERE c.embedding IS NOT NULL
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding, embedding, fetch_limit),
                ).fetchall()
            except Exception:
                logger.exception("向量检索失败，将回退到原文检索")
                vector_rows = []

        keyword_rows = conn.execute(
            """
            SELECT c.id, c.content, c.page_number, c.chunk_index, d.filename,
                   similarity(c.content, %s) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY similarity(c.content, %s) DESC
            LIMIT %s
            """,
            (query, query, fetch_limit),
        ).fetchall()

        fallback_rows: list[tuple] = []
        if not vector_rows:
            fallback_rows = conn.execute(
                """
                SELECT c.id, c.content, c.page_number, c.chunk_index, d.filename,
                       0.01 AS score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY d.created_at DESC, c.chunk_index
                LIMIT %s
                """,
                (fetch_limit,),
            ).fetchall()

    merged: dict[str, dict] = {}
    for row in [*vector_rows, *keyword_rows, *fallback_rows]:
        item_id = str(row[0])
        payload = {
            "id": item_id,
            "content": row[1],
            "page_number": row[2],
            "chunk_index": row[3],
            "filename": row[4],
            "score": float(row[5] or 0),
        }
        previous = merged.get(item_id)
        if previous is None or payload["score"] > previous["score"]:
            merged[item_id] = payload

    ranked = sorted(merged.values(), key=lambda item: item["score"], reverse=True)
    return ranked[:fetch_limit]


def _embed_in_batches(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        vectors.extend(embed_texts(texts[start : start + BATCH_SIZE]))
    return vectors


def _delete_all_documents(conn) -> None:
    rows = conn.execute("SELECT storage_path FROM documents").fetchall()
    conn.execute("DELETE FROM documents")
    for (storage_path,) in rows:
        path = Path(storage_path)
        if path.exists():
            path.unlink()


def _document_row(row) -> dict:
    return {
        "id": str(row[0]),
        "filename": row[1],
        "byte_size": row[2],
        "page_count": row[3],
        "chunk_count": row[4],
        "status": row[5],
        "error": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
    }
