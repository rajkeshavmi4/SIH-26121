from sqlalchemy.orm import Session
from ..models import Document
def get_document(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)
