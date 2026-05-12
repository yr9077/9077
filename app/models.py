from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScriptRecord(Base):
    __tablename__ = "script_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    dialect: Mapped[str] = mapped_column(String(20), nullable=False, default="mysql")
    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, default="none")
    risk_issues: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.utcnow()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    clarifications: Mapped[list["ClarificationSession"]] = relationship(
        "ClarificationSession", back_populates="script_record", cascade="all, delete-orphan"
    )


class ClarificationSession(Base):
    __tablename__ = "clarification_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    script_record_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("script_records.id"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.utcnow()
    )

    script_record: Mapped["ScriptRecord"] = relationship(
        "ScriptRecord", back_populates="clarifications"
    )
