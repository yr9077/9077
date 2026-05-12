import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ScriptRecord
from app.schemas import (
    GenerateRequest,
    GenerateResponse,
    PaginatedRecords,
    ScriptRecordResponse,
    ScriptRecordUpdate,
)
from app.services.sql_generator import SQLGeneratorService

router = APIRouter(prefix="/api", tags=["generate"])
_generator = SQLGeneratorService()


@router.post("/generate", response_model=GenerateResponse)
async def generate_sql(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await _generator.generate_and_validate(
            req.request_text, req.dialect, req.extra_context or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    record = ScriptRecord(
        request_text=req.request_text,
        dialect=req.dialect,
        generated_sql=result["sql"],
        risk_level=result["risk_level"],
        risk_issues=json.dumps(result["issues"]),
        status="pending",
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return GenerateResponse(
        record=ScriptRecordResponse.model_validate(record),
        message="SQL generated successfully.",
    )


@router.post("/regenerate/{record_id}", response_model=GenerateResponse)
async def regenerate_sql(record_id: int, db: AsyncSession = Depends(get_db)):
    result_db = await db.get(ScriptRecord, record_id)
    if not result_db:
        raise HTTPException(status_code=404, detail="Record not found.")

    result_db.status = "regenerating"
    await db.flush()

    try:
        result = await _generator.generate_and_validate(
            result_db.request_text, result_db.dialect
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result_db.generated_sql = result["sql"]
    result_db.risk_level = result["risk_level"]
    result_db.risk_issues = json.dumps(result["issues"])
    result_db.status = "pending"
    await db.flush()
    await db.refresh(result_db)
    return GenerateResponse(
        record=ScriptRecordResponse.model_validate(result_db),
        message="SQL regenerated successfully.",
    )


@router.get("/records", response_model=PaginatedRecords)
async def list_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    dialect: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ScriptRecord)
    if dialect:
        stmt = stmt.where(ScriptRecord.dialect == dialect)
    if status:
        stmt = stmt.where(ScriptRecord.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(ScriptRecord.created_at.desc())
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()

    return PaginatedRecords(
        items=[ScriptRecordResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/records/{record_id}", response_model=ScriptRecordResponse)
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await db.get(ScriptRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    return ScriptRecordResponse.model_validate(record)


@router.patch("/records/{record_id}", response_model=ScriptRecordResponse)
async def update_record(
    record_id: int,
    update: ScriptRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(ScriptRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    if update.status is not None:
        record.status = update.status
    if update.notes is not None:
        record.notes = update.notes
    await db.flush()
    await db.refresh(record)
    return ScriptRecordResponse.model_validate(record)
