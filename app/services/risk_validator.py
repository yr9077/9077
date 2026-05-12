import re
from typing import Any, Dict, List

import sqlparse


class RiskValidator:
    def validate(self, sql_text: str, dialect: str = "mysql") -> Dict[str, Any]:
        issues: List[Dict[str, str]] = []
        upper = sql_text.upper()

        # HIGH: DROP TABLE/DATABASE without IF EXISTS
        if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\b", upper):
            if "IF EXISTS" not in upper:
                issues.append(
                    {
                        "level": "high",
                        "category": "data_loss",
                        "message": "DROP statement without IF EXISTS check detected.",
                        "suggestion": "Add IF EXISTS to prevent errors and data loss on non-existent objects.",
                    }
                )
            else:
                issues.append(
                    {
                        "level": "medium",
                        "category": "data_loss",
                        "message": "DROP statement detected even with IF EXISTS.",
                        "suggestion": "Ensure you have a backup before dropping objects.",
                    }
                )

        # HIGH: DELETE without WHERE
        if re.search(r"\bDELETE\s+FROM\b", upper):
            stmt = re.sub(r"--[^\n]*", "", sql_text)
            if not re.search(r"\bWHERE\b", stmt.upper()):
                issues.append(
                    {
                        "level": "high",
                        "category": "data_loss",
                        "message": "DELETE statement without WHERE clause will delete all rows.",
                        "suggestion": "Add a WHERE clause to limit the rows affected.",
                    }
                )

        # HIGH: UPDATE without WHERE
        if re.search(r"\bUPDATE\b.+\bSET\b", upper, re.DOTALL):
            stmt = re.sub(r"--[^\n]*", "", sql_text)
            if not re.search(r"\bWHERE\b", stmt.upper()):
                issues.append(
                    {
                        "level": "high",
                        "category": "data_loss",
                        "message": "UPDATE statement without WHERE clause will update all rows.",
                        "suggestion": "Add a WHERE clause to limit the rows affected.",
                    }
                )

        # MEDIUM: TRUNCATE
        if re.search(r"\bTRUNCATE\b", upper):
            issues.append(
                {
                    "level": "medium",
                    "category": "data_loss",
                    "message": "TRUNCATE will remove all rows from the table.",
                    "suggestion": "Ensure you have a backup. Consider DELETE with WHERE instead.",
                }
            )

        # MEDIUM: ALTER TABLE (schema change)
        if re.search(r"\bALTER\s+TABLE\b", upper):
            issues.append(
                {
                    "level": "medium",
                    "category": "schema_change",
                    "message": "ALTER TABLE modifies the schema which may affect existing data.",
                    "suggestion": "Test on a staging environment first and ensure backward compatibility.",
                }
            )

        # LOW: CREATE TABLE without IF NOT EXISTS
        if re.search(r"\bCREATE\s+TABLE\b", upper):
            if "IF NOT EXISTS" not in upper:
                issues.append(
                    {
                        "level": "low",
                        "category": "safety",
                        "message": "CREATE TABLE without IF NOT EXISTS may fail if table exists.",
                        "suggestion": "Use CREATE TABLE IF NOT EXISTS to avoid errors.",
                    }
                )

        # LOW: INSERT without explicit column list
        if re.search(r"\bINSERT\s+INTO\s+\w+\s+VALUES\b", upper):
            issues.append(
                {
                    "level": "low",
                    "category": "best_practice",
                    "message": "INSERT without explicit column list is fragile.",
                    "suggestion": "Specify column names: INSERT INTO table (col1, col2) VALUES (...).",
                }
            )

        # LOW: Missing semicolon
        stripped = sql_text.strip()
        if stripped and not stripped.endswith(";"):
            issues.append(
                {
                    "level": "low",
                    "category": "lint",
                    "message": "SQL statement does not end with a semicolon.",
                    "suggestion": "Add a semicolon at the end of the statement.",
                }
            )

        # LOW: SELECT * (full table scan info)
        if re.search(r"\bSELECT\s+\*\b", upper):
            issues.append(
                {
                    "level": "low",
                    "category": "performance",
                    "message": "SELECT * fetches all columns which may cause performance issues on large tables.",
                    "suggestion": "Select only the columns you need instead of SELECT *.",
                }
            )

        risk_level = self._compute_risk_level(issues)
        return {"risk_level": risk_level, "issues": issues}

    def _compute_risk_level(self, issues: List[Dict[str, str]]) -> str:
        levels = [i["level"] for i in issues]
        if "high" in levels:
            return "high"
        if "medium" in levels:
            return "medium"
        if "low" in levels:
            return "low"
        return "none"

    def lint_sql(self, sql_text: str) -> str:
        sql = sql_text.strip()
        sql = re.sub(r"[ \t]+", " ", sql)
        try:
            sql = sqlparse.format(
                sql,
                reindent=True,
                keyword_case="upper",
                strip_whitespace=False,
            )
        except Exception:
            pass
        sql = sql.strip()
        if sql and not sql.endswith(";"):
            sql += ";"
        return sql
