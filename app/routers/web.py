import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ScriptRecord

router = APIRouter(tags=["web"])
_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)
templates = Jinja2Templates(env=_jinja_env)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(ScriptRecord))).scalar_one()
    approved = (
        await db.execute(
            select(func.count()).select_from(ScriptRecord).where(ScriptRecord.status == "approved")
        )
    ).scalar_one()
    high_risk = (
        await db.execute(
            select(func.count())
            .select_from(ScriptRecord)
            .where(ScriptRecord.risk_level == "high")
        )
    ).scalar_one()
    recent_stmt = (
        select(ScriptRecord).order_by(ScriptRecord.created_at.desc()).limit(5)
    )
    recent = (await db.execute(recent_stmt)).scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "total": total,
            "approved": approved,
            "high_risk": high_risk,
            "recent": recent,
        },
    )


@router.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(ScriptRecord).order_by(ScriptRecord.created_at.desc()).limit(50)
    records = (await db.execute(stmt)).scalars().all()
    return templates.TemplateResponse(
        "history.html", {"request": request, "records": records}
    )


@router.get("/review/{record_id}", response_class=HTMLResponse)
async def review_page(record_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    record = await db.get(ScriptRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    try:
        issues = json.loads(record.risk_issues)
    except Exception:
        issues = []
    return templates.TemplateResponse(
        "review.html",
        {"request": request, "record": record, "issues": issues},
    )
