"""MAJE – Costs Routes"""
from fastapi import APIRouter
from core.cost_tracker import cost_tracker
from config.api_keys import COST_SETTINGS

router = APIRouter()


@router.get("/today")
async def get_today_costs():
    total_eur = await cost_tracker.get_today_total_eur()
    breakdown = await cost_tracker.get_daily_breakdown()
    limit = COST_SETTINGS.get("daily_limit_eur", 2.0)
    return {
        "total_eur": round(total_eur, 4),
        "limit_eur": limit,
        "used_pct": round((total_eur / limit * 100) if limit > 0 else 0, 1),
        "breakdown": breakdown,
    }


@router.get("/monthly")
async def get_monthly_costs():
    return {"monthly": await cost_tracker.get_monthly_totals()}


@router.get("/history/{date}")
async def get_costs_for_date(date: str):
    breakdown = await cost_tracker.get_daily_breakdown(target_date=date)
    return {"date": date, "breakdown": breakdown}
