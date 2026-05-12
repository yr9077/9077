import re

from app.config import settings
from app.services.dialect_adapter import DialectAdapter

_adapter = DialectAdapter()


class LLMService:
    async def generate_sql(
        self, request_text: str, dialect: str, extra_context: str = ""
    ) -> str:
        if settings.LLM_PROVIDER == "openai":
            return await self._openai_generate(request_text, dialect, extra_context)
        return await self._mock_generate(request_text, dialect)

    async def _mock_generate(self, request_text: str, dialect: str) -> str:
        hints = _adapter.get_dialect_hints(dialect)
        lower = request_text.lower()

        # Detect intent and extract a table name hint
        table_name = self._extract_table_name(request_text) or "sample_table"

        if any(kw in lower for kw in ["create table", "建表", "创建表", "new table"]):
            return self._gen_create_table(table_name, dialect, hints)

        if any(kw in lower for kw in ["select", "查询", "查找", "fetch", "get all", "list"]):
            return self._gen_select(table_name, dialect)

        if any(kw in lower for kw in ["insert", "插入", "新增", "add record"]):
            return self._gen_insert(table_name, dialect)

        if any(kw in lower for kw in ["update", "更新", "修改", "change"]):
            return self._gen_update(table_name, dialect)

        if any(kw in lower for kw in ["delete", "删除", "remove record"]):
            return self._gen_delete(table_name, dialect)

        if any(kw in lower for kw in ["index", "索引", "create index"]):
            return self._gen_index(table_name, dialect)

        if any(kw in lower for kw in ["alter", "add column", "drop column", "modify"]):
            return self._gen_alter(table_name, dialect)

        # Default: CREATE TABLE
        return self._gen_create_table(table_name, dialect, hints)

    def _extract_table_name(self, text: str) -> str:
        patterns = [
            r"\b(?:table|表)\s+[`'\"]?(\w+)[`'\"]?",
            r"\b(?:named|called|for)\s+[`'\"]?(\w+)[`'\"]?",
            r"[`'\"](\w+)[`'\"]",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).lower()
        # Grab the last capitalized word as a table name hint
        words = re.findall(r"[A-Z][a-z]+", text)
        if words:
            return words[-1].lower() + "s"
        return ""

    def _gen_create_table(self, table: str, dialect: str, hints: dict) -> str:
        if dialect == "postgresql":
            return (
                f"CREATE TABLE IF NOT EXISTS {table} (\n"
                f"    id SERIAL PRIMARY KEY,\n"
                f"    name VARCHAR(255) NOT NULL,\n"
                f"    description TEXT,\n"
                f"    status VARCHAR(50) DEFAULT 'active',\n"
                f"    created_at TIMESTAMP DEFAULT NOW(),\n"
                f"    updated_at TIMESTAMP DEFAULT NOW()\n"
                f");"
            )
        elif dialect == "sqlite":
            return (
                f"CREATE TABLE IF NOT EXISTS {table} (\n"
                f"    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                f"    name TEXT NOT NULL,\n"
                f"    description TEXT,\n"
                f"    status TEXT DEFAULT 'active',\n"
                f"    created_at TEXT DEFAULT (datetime('now')),\n"
                f"    updated_at TEXT DEFAULT (datetime('now'))\n"
                f");"
            )
        else:
            return (
                f"CREATE TABLE IF NOT EXISTS {table} (\n"
                f"    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n"
                f"    name VARCHAR(255) NOT NULL,\n"
                f"    description TEXT,\n"
                f"    status VARCHAR(50) DEFAULT 'active',\n"
                f"    created_at DATETIME DEFAULT NOW(),\n"
                f"    updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()\n"
                f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
            )

    def _gen_select(self, table: str, dialect: str) -> str:
        return (
            f"SELECT id, name, description, status, created_at\n"
            f"FROM {table}\n"
            f"WHERE status = 'active'\n"
            f"ORDER BY created_at DESC\n"
            f"LIMIT 100;"
        )

    def _gen_insert(self, table: str, dialect: str) -> str:
        return (
            f"INSERT INTO {table} (name, description, status)\n"
            f"VALUES ('Example Name', 'Example description', 'active');"
        )

    def _gen_update(self, table: str, dialect: str) -> str:
        return (
            f"UPDATE {table}\n"
            f"SET status = 'inactive',\n"
            f"    updated_at = NOW()\n"
            f"WHERE id = 1;"
        )

    def _gen_delete(self, table: str, dialect: str) -> str:
        return f"DELETE FROM {table}\nWHERE id = 1 AND status = 'inactive';"

    def _gen_index(self, table: str, dialect: str) -> str:
        return (
            f"CREATE INDEX IF NOT EXISTS idx_{table}_status\n"
            f"ON {table} (status);\n\n"
            f"CREATE INDEX IF NOT EXISTS idx_{table}_created_at\n"
            f"ON {table} (created_at);"
        )

    def _gen_alter(self, table: str, dialect: str) -> str:
        if dialect == "postgresql":
            col_def = "VARCHAR(255)"
        elif dialect == "sqlite":
            col_def = "TEXT"
        else:
            col_def = "VARCHAR(255)"
        return f"ALTER TABLE {table}\nADD COLUMN new_column {col_def};"

    async def _openai_generate(
        self, request_text: str, dialect: str, extra_context: str = ""
    ) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        system_prompt = (
            f"You are a SQL expert specializing in {dialect.upper()} databases. "
            "Generate clean, efficient, and safe SQL scripts based on the user's request. "
            "Always use IF NOT EXISTS for CREATE TABLE, use WHERE clauses for DELETE/UPDATE, "
            "and follow best practices. Return only the SQL code without explanation."
        )
        user_prompt = request_text
        if extra_context:
            user_prompt += f"\n\nAdditional context: {extra_context}"

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
