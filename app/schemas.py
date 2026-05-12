from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    request_text: str = Field(..., min_length=1)
    dialect: Literal["mysql", "postgresql", "sqlite"] = "mysql"
    extra_context: Optional[str] = None


class ValidateRequest(BaseModel):
    sql_text: str = Field(..., min_length=1)
    dialect: Literal["mysql", "postgresql", "sqlite"] = "mysql"


class RiskIssue(BaseModel):
    level: Literal["none", "low", "medium", "high"]
    category: str
    message: str
    suggestion: str


class ValidateResponse(BaseModel):
    sql_text: str
    dialect: str
    risk_level: Literal["none", "low", "medium", "high"]
    issues: List[RiskIssue]
    linted_sql: str


class ScriptRecordCreate(BaseModel):
    request_text: str = Field(..., min_length=1)
    dialect: Literal["mysql", "postgresql", "sqlite"] = "mysql"
    extra_context: Optional[str] = None


class ScriptRecordResponse(BaseModel):
    id: int
    request_text: str
    dialect: str
    generated_sql: str
    risk_level: str
    risk_issues: str
    status: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ScriptRecordUpdate(BaseModel):
    status: Optional[Literal["pending", "approved", "rejected", "regenerating"]] = None
    notes: Optional[str] = None


class GenerateResponse(BaseModel):
    record: ScriptRecordResponse
    message: str


class ClarificationCreate(BaseModel):
    script_record_id: int
    question: str = Field(..., min_length=1)
    answer: Optional[str] = None


class ClarificationResponse(BaseModel):
    id: int
    script_record_id: int
    question: str
    answer: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedRecords(BaseModel):
    items: List[ScriptRecordResponse]
    total: int
    page: int
    per_page: int
