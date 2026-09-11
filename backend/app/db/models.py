from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    Text,
    UniqueConstraint,
)

from backend.app.db.database import Base


# =========================================================
# Documents Table
# =========================================================

class Document(Base):
    __tablename__ = "documents"

    __table_args__ = (
        UniqueConstraint(
            "document_name",
            name="uq_documents_document_name",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_name = Column(
        Text,
        nullable=False,
    )

    document_type = Column(
        Text,
        nullable=False,
    )

    processing_status = Column(
        Text,
        nullable=False,
    )

    file_validation_json = Column(
        Text,
        nullable=True,
    )

    extracted_text = Column(
        Text,
        nullable=True,
    )

    extracted_data_json = Column(
        Text,
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    validation_json = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )