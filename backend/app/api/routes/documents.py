import hashlib
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...core.config import settings
from ...db import get_db
from ...ingestion import extract_document_pages, extract_pages
from ...models import Document
from ...schemas.document import DocumentExtractionResponse, DocumentResponse, DocumentReviewUpdate
router = APIRouter(prefix="/api/documents", tags=["documents"])
def _response(document: Document, candidates: list[dict] | None = None):
    payload = DocumentResponse.model_validate(document).model_dump()
    if candidates is not None:
        payload["candidates"] = candidates
    return payload
@router.post("/upload", response_model=DocumentExtractionResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or "upload.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".pdf"}:
        raise HTTPException(400, "Only PDF and TXT reports are supported")
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "File exceeds the configured upload size limit")
    digest = hashlib.sha256(content).hexdigest()
    existing = db.scalar(select(Document).where(Document.content_sha256 == digest))
    if existing:
        raise HTTPException(409, f"Duplicate document import: {existing.document_id}")
    try:
        pages = extract_pages(filename, content)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    document = Document(document_id=f"doc-{uuid4().hex[:12]}", filename=filename, document_type="report", content_sha256=digest, file_size_bytes=len(content), mime_type=file.content_type or ("application/pdf" if suffix == ".pdf" else "text/plain"), data_origin="uploaded", is_synthetic=False, provenance="uploaded by user", extracted_text="\n".join(pages), page_count=len(pages), extraction_status="extracted" if any(page.strip() for page in pages) else "scanned_unreadable", review_status="needs_review")
    db.add(document); db.commit(); db.refresh(document)
    return _response(document, extract_document_pages(pages))
@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.created_at.desc())).all()
def _find_document(document_id: str, db: Session) -> Document:
    document = db.scalar(select(Document).where(Document.document_id == document_id))
    if not document:
        raise HTTPException(404, "Document not found")
    return document
@router.get("/{document_id}/viewer", response_class=PlainTextResponse)
def view_document(document_id: str, db: Session = Depends(get_db)):
    return _find_document(document_id, db).extracted_text or ""
@router.post("/{document_id}/extract", response_model=DocumentExtractionResponse)
def extract_document(document_id: str, db: Session = Depends(get_db)):
    document = _find_document(document_id, db)
    pages = (document.extracted_text or "").split("\n")
    candidates = extract_document_pages(pages) if document.extracted_text else []
    document.extraction_status = "extracted" if candidates else ("scanned_unreadable" if not document.extracted_text else "no_candidates")
    document.extraction_confidence = round(sum(item["confidence"] for item in candidates) / len(candidates), 2) if candidates else 0.0
    document.review_status = "needs_review"
    db.commit(); db.refresh(document)
    return _response(document, candidates)
@router.patch("/{document_id}", response_model=DocumentExtractionResponse)
def review_document(document_id: str, update: DocumentReviewUpdate, db: Session = Depends(get_db)):
    document = _find_document(document_id, db)
    if update.extracted_text is not None:
        document.extracted_text = update.extracted_text
        document.extraction_status = "edited"
        document.extraction_confidence = None
    if update.review_status is not None:
        document.review_status = update.review_status
    db.commit(); db.refresh(document)
    pages = (document.extracted_text or "").split("\n")
    return _response(document, extract_document_pages(pages) if document.extracted_text else [])
@router.get("/{document_id}", response_model=DocumentExtractionResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    document = _find_document(document_id, db)
    pages = (document.extracted_text or "").split("\n")
    return _response(document, extract_document_pages(pages) if document.extracted_text else [])
