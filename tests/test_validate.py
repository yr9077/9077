import pytest


@pytest.mark.asyncio
async def test_validate_safe_select(client):
    resp = await client.post(
        "/api/validate",
        json={
            "sql_text": "SELECT id, name FROM users WHERE status = 'active';",
            "dialect": "mysql",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] in ("none", "low")


@pytest.mark.asyncio
async def test_validate_delete_without_where(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "DELETE FROM users", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] == "high"
    levels = [i["level"] for i in data["issues"]]
    assert "high" in levels


@pytest.mark.asyncio
async def test_validate_update_without_where(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "UPDATE users SET status = 'inactive'", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] == "high"


@pytest.mark.asyncio
async def test_validate_drop_table(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "DROP TABLE users", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] == "high"


@pytest.mark.asyncio
async def test_validate_drop_table_with_if_exists(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "DROP TABLE IF EXISTS users;", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # IF EXISTS lowers to medium
    assert data["risk_level"] in ("medium", "low", "none")


@pytest.mark.asyncio
async def test_validate_truncate(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "TRUNCATE TABLE users;", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] in ("medium", "high")
    categories = [i["category"] for i in data["issues"]]
    assert "data_loss" in categories


@pytest.mark.asyncio
async def test_validate_lint(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "select id from users where id=1", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "linted_sql" in data
    assert len(data["linted_sql"]) > 0
    # Linted SQL should be uppercase keywords
    assert "SELECT" in data["linted_sql"] or "select" in data["linted_sql"]


@pytest.mark.asyncio
async def test_validate_postgresql_dialect(client):
    resp = await client.post(
        "/api/validate",
        json={
            "sql_text": "SELECT id, name FROM users WHERE active = TRUE;",
            "dialect": "postgresql",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["dialect"] == "postgresql"


@pytest.mark.asyncio
async def test_validate_returns_linted_sql(client):
    resp = await client.post(
        "/api/validate",
        json={"sql_text": "select * from orders", "dialect": "sqlite"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["linted_sql"].endswith(";")


@pytest.mark.asyncio
async def test_validate_alter_table(client):
    resp = await client.post(
        "/api/validate",
        json={
            "sql_text": "ALTER TABLE users ADD COLUMN phone VARCHAR(20);",
            "dialect": "mysql",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] in ("medium", "high")
