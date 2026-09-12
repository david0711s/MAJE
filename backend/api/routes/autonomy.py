"""MAJE – Autonomy Mode Routes"""
from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.agent_loop import agent_loop
from core.cost_tracker import cost_tracker
from core.task_state import TaskMode, task_manager
from storage.redis_client import redis_client
from config.api_keys import COST_SETTINGS

router = APIRouter()

AUTONOMY_KEY = "autonomy:state"
AUTONOMY_FOCUS_KEY = "autonomy:focus"
AUTONOMY_INTERVAL_KEY = "autonomy:interval_minutes"
AUTONOMY_LIMIT_KEY = "autonomy:cost_limit_eur"


async def _get_text(key: str) -> Optional[str]:
    raw = await redis_client.get(key)
    if raw is None:
        return None
    return raw.decode() if isinstance(raw, bytes) else str(raw)


@router.get("/status")
async def get_autonomy_status():
    state = (await _get_text(AUTONOMY_KEY)) or "off"
    focus = (await _get_text(AUTONOMY_FOCUS_KEY)) or ""
    interval = int((await _get_text(AUTONOMY_INTERVAL_KEY)) or "30")
    limit = float((await _get_text(AUTONOMY_LIMIT_KEY)) or COST_SETTINGS.get("autonomy_mode_daily_limit_eur", 0.5))
    cost_ok = await cost_tracker.check_limit(is_autonomy=True)

    history = [t for t in await task_manager.list_tasks(limit=100) if t.get("mode") == "autonomy"][:10]

    active = state == "on"
    return {
        "active": active,
        "is_running": active,
        "focus": focus,
        "current_focus": focus,
        "cost_limit_ok": cost_ok,
        "cost_limit_eur": limit,
        "interval_minutes": interval,
        "history": history,
    }


class AutonomyStart(BaseModel):
    focus: Optional[str] = ""
    cost_limit_eur: Optional[float] = None
    interval_minutes: Optional[int] = None
    confirmed: bool = True  # the app toggles explicitly; keep a soft safety default


class FocusUpdate(BaseModel):
    focus: Optional[str] = ""


@router.post("/start")
async def start_autonomy(body: AutonomyStart):
    if not body.confirmed:
        raise HTTPException(400, "Starting autonomy mode requires confirmed=true")

    limit = body.cost_limit_eur if body.cost_limit_eur is not None else COST_SETTINGS.get("autonomy_mode_daily_limit_eur", 0.5)
    if limit <= 0:
        raise HTTPException(400, "Autonomy mode requires an active cost limit > 0. Set it in Settings.")

    if not await cost_tracker.check_limit(is_autonomy=True):
        raise HTTPException(400, "Daily autonomy cost limit already reached. Try again tomorrow.")

    interval = max(5, min(int(body.interval_minutes or 30), 1440))

    await redis_client.set(AUTONOMY_KEY, "on")
    await redis_client.set(AUTONOMY_INTERVAL_KEY, str(interval))
    await redis_client.set(AUTONOMY_LIMIT_KEY, str(limit))
    if body.focus:
        await redis_client.set(AUTONOMY_FOCUS_KEY, body.focus)

    asyncio.create_task(_autonomy_loop(body.focus or "", interval))
    return {"started": True, "focus": body.focus, "interval_minutes": interval}


@router.post("/stop")
async def stop_autonomy():
    await redis_client.set(AUTONOMY_KEY, "off")
    await task_manager.set_global_stop(True)
    await asyncio.sleep(0.1)
    await task_manager.set_global_stop(False)
    return {"stopped": True}


@router.post("/focus")
@router.put("/focus")
async def update_focus(body: FocusUpdate):
    if body.focus:
        await redis_client.set(AUTONOMY_FOCUS_KEY, body.focus)
    return {"focus": body.focus}


async def _autonomy_loop(focus: str, interval_minutes: int = 30):
    """Background autonomy loop – creates & runs self-directed learning tasks."""
    while True:
        state = await _get_text(AUTONOMY_KEY)
        if state != "on":
            break

        if not await cost_tracker.check_limit(is_autonomy=True):
            await redis_client.set(AUTONOMY_KEY, "off")
            break

        goal = (
            f"Explore and learn something interesting or useful. "
            f"Focus area: {focus or 'anything relevant to helping the user'}. "
            f"Document findings in memory."
        )
        task = task_manager.create(mode=TaskMode.AUTONOMY, goal=goal)
        await task_manager.save(task)

        async def emit(payload: dict, _task=task):
            # Autonomy runs unattended – events are persisted with the task state.
            pass

        try:
            await agent_loop.run_agent(task, emit=emit)
        except Exception:
            pass

        await asyncio.sleep(max(30, interval_minutes * 60))
