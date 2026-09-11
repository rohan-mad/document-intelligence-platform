from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from backend.app.core.database import Base


class Document(Base):

    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_name = Column(
        String(255),
        index=True,
        nullable=False
    )

    document_type = Column(
        String(50),
        nullable=False
    )

    processing_status = Column(
        String(20),
        nullable=False
    )

    result_json = Column(
        Text,
        nullable=False
    )

    ocr_used = Column(
        String(10),
        nullable=False
    )

    processed_at = Column(
        DateTime,
        default=datetime.utcnow
    )