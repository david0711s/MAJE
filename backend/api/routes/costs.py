"""MAJE – Costs Routes"""
from __future__ import annotations

from fastapi import APIRouter

from core.cost_tracker import cost_tracker
from config.api_keys import COST_SETTINGS

router = APIRouter()


@router.get("/today")
async def get_today_costs():
    """App-compatible daily cost summary."""
    return await cost_tracker.get_today_costs()


@router.get("/month")
async def get_month_costs():
    """Aggregated 30-day cost summary."""
    monthly = await cost_tracker.get_monthly_totals()
    total_eur = round(sum(float(d.get("cost_eur", 0.0)) for d in monthly), 6)
    daily_limit = float(COST_SETTINGS.get("daily_limit_eur", 2.0))
    return {
        "total_eur": total_eur,
        "monthly_limit_eur": round(daily_limit * 30, 2),
        "total_tokens": 0,
        "days": monthly,
    }


@router.get("/monthly")
async def get_monthly_costs():
    return {"monthly": await cost_tracker.get_monthly_totals()}


@router.get("/history/{date}")
async def get_costs_for_date(date: str):
    return {"date": date, "breakdown": await cost_tracker.get_daily_breakdown(target_date=date)}
