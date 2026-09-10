from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import require_admin
from app.core.config import settings
from app.ingest.pipeline import (
    delete_document,
    get_document,
    ingest_pdf,
    list_chunks,
    list_documents,
)

router = APIRouter()


class LoginBody(BaseModel):
    token: str


@router.post("/login")
async def login(body: LoginBody):
    if body.token != settings.admin_token:
        raise HTTPException(status_code=401, detail="管理令牌无效")
    response = JSONResponse({"ok": True})
    response.set_cookie(
        "admin_token",
        body.token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/documents")
def documents(_: str = Depends(require_admin)):
    return {"items": list_documents()}


@router.get("/documents/{document_id}")
def document_detail(document_id: str, _: str = Depends(require_admin)):
    document = get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"document": document, "chunks": list_chunks(document_id)}


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    replace_existing: str = Form("false"),
    _: str = Depends(require_admin),
):
    filename = file.filename or "resume.pdf"
    data = await file.read()
    should_replace = replace_existing.strip().lower() in {"1", "true", "on", "yes"}
    try:
        document = ingest_pdf(
            filename,
            data,
            replace_existing=should_replace,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return document


@router.delete("/documents/{document_id}")
def remove_document(document_id: str, _: str = Depends(require_admin)):
    if not delete_document(document_id):
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"ok": True}
