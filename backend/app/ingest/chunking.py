from collections.abc import Iterable


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    return _split_recursive(normalized, chunk_size, overlap, separators)


def split_pages(
    pages: Iterable[tuple[int, str]],
    chunk_size: int,
    overlap: int,
) -> list[tuple[int, str]]:
    chunks: list[tuple[int, str]] = []
    for page_number, text in pages:
        for part in split_text(text, chunk_size, overlap):
            chunks.append((page_number, part))
    return chunks


def _split_recursive(
    text: str,
    chunk_size: int,
    overlap: int,
    separators: list[str],
) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    separator = separators[0]
    rest = separators[1:]
    pieces = text.split(separator) if separator else list(text)
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        candidate = piece if not current else f"{current}{separator}{piece}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current.strip():
            chunks.append(current.strip())
        if rest and len(piece) > chunk_size:
            chunks.extend(_split_recursive(piece, chunk_size, overlap, rest))
            current = ""
        else:
            current = piece

    if current.strip():
        chunks.append(current.strip())

    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    merged: list[str] = []
    for index, chunk in enumerate(chunks):
        if index == 0:
            merged.append(chunk)
            continue
        prefix = chunks[index - 1][-overlap:]
        merged.append(f"{prefix}{chunk}" if not chunk.startswith(prefix) else chunk)
    return merged
