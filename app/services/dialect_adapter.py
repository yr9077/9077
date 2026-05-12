from typing import Dict


class DialectAdapter:
    SUPPORTED = ["mysql", "postgresql", "sqlite"]

    def get_dialect_hints(self, dialect: str) -> Dict[str, str]:
        hints = {
            "mysql": {
                "auto_increment": "AUTO_INCREMENT",
                "string_type": "VARCHAR",
                "bool_type": "TINYINT(1)",
                "now_func": "NOW()",
                "engine": "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4",
                "pk_suffix": "INT NOT NULL AUTO_INCREMENT PRIMARY KEY",
            },
            "postgresql": {
                "auto_increment": "SERIAL",
                "string_type": "VARCHAR",
                "bool_type": "BOOLEAN",
                "now_func": "NOW()",
                "engine": "",
                "pk_suffix": "SERIAL PRIMARY KEY",
            },
            "sqlite": {
                "auto_increment": "AUTOINCREMENT",
                "string_type": "TEXT",
                "bool_type": "INTEGER",
                "now_func": "datetime('now')",
                "engine": "",
                "pk_suffix": "INTEGER PRIMARY KEY AUTOINCREMENT",
            },
        }
        return hints.get(dialect, hints["mysql"])

    def adapt_sql(self, sql: str, dialect: str) -> str:
        if dialect == "mysql":
            sql = sql.replace("AUTOINCREMENT", "AUTO_INCREMENT")
            sql = sql.replace("BOOLEAN", "TINYINT(1)")
            sql = sql.replace(" SERIAL", " INT NOT NULL AUTO_INCREMENT")
            sql = sql.replace("SMALLINT", "INT")
        elif dialect == "postgresql":
            sql = sql.replace("AUTO_INCREMENT", "")
            sql = sql.replace(" INT NOT NULL AUTO_INCREMENT", " SERIAL")
            sql = sql.replace("AUTOINCREMENT", "")
            sql = sql.replace("TINYINT(1)", "BOOLEAN")
            sql = sql.replace("TINYINT", "SMALLINT")
            sql = sql.replace("ENGINE=InnoDB DEFAULT CHARSET=utf8mb4", "")
        elif dialect == "sqlite":
            sql = sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
            sql = sql.replace("ENGINE=InnoDB DEFAULT CHARSET=utf8mb4", "")
        return sql

    def validate_dialect(self, dialect: str) -> None:
        if dialect not in self.SUPPORTED:
            raise ValueError(
                f"Unsupported dialect '{dialect}'. Supported: {', '.join(self.SUPPORTED)}"
            )
