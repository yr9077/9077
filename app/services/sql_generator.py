from typing import Any, Dict

from app.services.dialect_adapter import DialectAdapter
from app.services.llm_service import LLMService
from app.services.risk_validator import RiskValidator

_llm = LLMService()
_validator = RiskValidator()
_adapter = DialectAdapter()


class SQLGeneratorService:
    async def generate_and_validate(
        self,
        request_text: str,
        dialect: str,
        extra_context: str = "",
    ) -> Dict[str, Any]:
        _adapter.validate_dialect(dialect)

        raw_sql = await _llm.generate_sql(request_text, dialect, extra_context)
        adapted_sql = _adapter.adapt_sql(raw_sql, dialect)
        validation = _validator.validate(adapted_sql, dialect)
        linted = _validator.lint_sql(adapted_sql)

        return {
            "sql": adapted_sql,
            "linted_sql": linted,
            "risk_level": validation["risk_level"],
            "issues": validation["issues"],
        }
