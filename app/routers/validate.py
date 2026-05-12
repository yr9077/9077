from fastapi import APIRouter

from app.schemas import RiskIssue, ValidateRequest, ValidateResponse
from app.services.dialect_adapter import DialectAdapter
from app.services.risk_validator import RiskValidator

router = APIRouter(prefix="/api", tags=["validate"])
_validator = RiskValidator()
_adapter = DialectAdapter()


@router.post("/validate", response_model=ValidateResponse)
async def validate_sql(req: ValidateRequest):
    result = _validator.validate(req.sql_text, req.dialect)
    linted = _validator.lint_sql(req.sql_text)
    issues = [RiskIssue(**i) for i in result["issues"]]
    return ValidateResponse(
        sql_text=req.sql_text,
        dialect=req.dialect,
        risk_level=result["risk_level"],
        issues=issues,
        linted_sql=linted,
    )
