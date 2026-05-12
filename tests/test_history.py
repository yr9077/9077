import pytest


@pytest.mark.asyncio
async def test_get_history(client):
    resp = await client.get("/api/history")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_history_pagination(client):
    resp = await client.get("/api/history?page=1&per_page=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["per_page"] == 5
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_delete_history(client):
    # First create a record to delete
    create_resp = await client.post(
        "/api/generate",
        json={"request_text": "Delete test record", "dialect": "mysql"},
    )
    assert create_resp.status_code == 200
    record_id = create_resp.json()["record"]["id"]

    del_resp = await client.delete(f"/api/history/{record_id}")
    assert del_resp.status_code == 200
    data = del_resp.json()
    assert "rejected" in data["message"]

    # Verify it's marked rejected
    get_resp = await client.get(f"/api/records/{record_id}")
    assert get_resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_delete_history_not_found(client):
    resp = await client.delete("/api/history/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_history(client):
    resp = await client.get("/api/history/export")
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    assert "total" in data
    assert isinstance(data["records"], list)
    assert data["total"] == len(data["records"])


@pytest.mark.asyncio
async def test_export_history_structure(client):
    # Create a record first to ensure export has content
    await client.post(
        "/api/generate",
        json={"request_text": "Export test query", "dialect": "postgresql"},
    )
    resp = await client.get("/api/history/export")
    assert resp.status_code == 200
    data = resp.json()
    if data["records"]:
        rec = data["records"][0]
        assert "id" in rec
        assert "request_text" in rec
        assert "dialect" in rec
        assert "generated_sql" in rec
        assert "risk_level" in rec
        assert "status" in rec
        assert "created_at" in rec
