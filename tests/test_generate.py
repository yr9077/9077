import pytest


@pytest.mark.asyncio
async def test_generate_mysql(client):
    resp = await client.post(
        "/api/generate",
        json={"request_text": "Create a users table", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "record" in data
    assert data["record"]["dialect"] == "mysql"


@pytest.mark.asyncio
async def test_generate_postgresql(client):
    resp = await client.post(
        "/api/generate",
        json={"request_text": "Create a products table", "dialect": "postgresql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["dialect"] == "postgresql"


@pytest.mark.asyncio
async def test_generate_sqlite(client):
    resp = await client.post(
        "/api/generate",
        json={"request_text": "Create a orders table", "dialect": "sqlite"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["dialect"] == "sqlite"


@pytest.mark.asyncio
async def test_generate_returns_sql(client):
    resp = await client.post(
        "/api/generate",
        json={"request_text": "Select all active users", "dialect": "mysql"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["record"]["generated_sql"]) > 0


@pytest.mark.asyncio
async def test_generate_invalid_dialect(client):
    resp = await client.post(
        "/api/generate",
        json={"request_text": "Create a table", "dialect": "oracle"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_records(client):
    resp = await client.get("/api/records")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_record_by_id(client):
    # First create a record
    create_resp = await client.post(
        "/api/generate",
        json={"request_text": "Insert into logs table", "dialect": "mysql"},
    )
    record_id = create_resp.json()["record"]["id"]

    resp = await client.get(f"/api/records/{record_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == record_id


@pytest.mark.asyncio
async def test_get_record_not_found(client):
    resp = await client.get("/api/records/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_record_status(client):
    create_resp = await client.post(
        "/api/generate",
        json={"request_text": "Update user status", "dialect": "mysql"},
    )
    record_id = create_resp.json()["record"]["id"]

    resp = await client.patch(
        f"/api/records/{record_id}",
        json={"status": "approved", "notes": "Looks good"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["notes"] == "Looks good"


@pytest.mark.asyncio
async def test_regenerate(client):
    create_resp = await client.post(
        "/api/generate",
        json={"request_text": "Create an index on email column", "dialect": "mysql"},
    )
    record_id = create_resp.json()["record"]["id"]

    resp = await client.post(f"/api/regenerate/{record_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["id"] == record_id
    assert len(data["record"]["generated_sql"]) > 0


@pytest.mark.asyncio
async def test_regenerate_not_found(client):
    resp = await client.post("/api/regenerate/999999")
    assert resp.status_code == 404
