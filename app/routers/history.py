import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ScriptRecord
from app.schemas import PaginatedRecords, ScriptRecordResponse

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=PaginatedRecords)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ScriptRecord).order_by(ScriptRecord.created_at.desc())
    count_stmt = select(func.count()).select_from(ScriptRecord)
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return PaginatedRecords(
        items=[ScriptRecordResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.delete("/{record_id}")
async def delete_history(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await db.get(ScriptRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    record.status = "rejected"
    await db.commit()
    return {"message": f"Record {record_id} marked as rejected."}


@router.get("/export")
async def export_history(db: AsyncSession = Depends(get_db)):
    stmt = select(ScriptRecord).order_by(ScriptRecord.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    data: List[dict] = []
    for r in rows:
        data.append(
            {
                "id": r.id,
                "request_text": r.request_text,
                "dialect": r.dialect,
                "generated_sql": r.generated_sql,
                "risk_level": r.risk_level,
                "risk_issues": json.loads(r.risk_issues),
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
                "notes": r.notes,
            }
        )
    return JSONResponse(content={"records": data, "total": len(data)})
