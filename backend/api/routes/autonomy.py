"""MAJE – Autonomy Mode Routes"""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.task_state import TaskMode, task_manager
from core.agent_loop import agent_loop
from core.cost_tracker import cost_tracker
from storage.redis_client import redis_client

router = APIRouter()

AUTONOMY_KEY = "autonomy:state"
AUTONOMY_FOCUS_KEY = "autonomy:focus"


@router.get("/status")
async def get_autonomy_status():
    """Get current autonomy mode state."""
    raw = await redis_client.get(AUTONOMY_KEY)
    focus_raw = await redis_client.get(AUTONOMY_FOCUS_KEY)
    state = raw.decode() if raw else "off"
    focus = focus_raw.decode() if focus_raw else ""
    cost_ok = await cost_tracker.check_limit(is_autonomy=True)

    return {
        "active": state == "on",
        "focus": focus,
        "cost_limit_ok": cost_ok,
    }


class AutonomyStart(BaseModel):
    focus: Optional[str] = ""
    confirmed: bool = False  # Must explicitly confirm


@router.post("/start")
async def start_autonomy(body: AutonomyStart):
    """Start autonomy mode. Requires active cost limit and explicit confirmation."""
    if not body.confirmed:
        raise HTTPException(400, "Starting autonomy mode requires confirmed=true")

    from config.api_keys import COST_SETTINGS
    limit = COST_SETTINGS.get("autonomy_mode_daily_limit_eur", 0.5)
    if limit <= 0:
        raise HTTPException(400, "Autonomy mode requires an active cost limit > 0. Set it in Settings.")

    cost_ok = await cost_tracker.check_limit(is_autonomy=True)
    if not cost_ok:
        raise HTTPException(400, "Daily autonomy cost limit already reached. Try again tomorrow.")

    await redis_client.set(AUTONOMY_KEY, "on")
    if body.focus:
        await redis_client.set(AUTONOMY_FOCUS_KEY, body.focus)

    # Start background autonomy loop
    asyncio.create_task(_autonomy_loop(body.focus or ""))

    return {"started": True, "focus": body.focus}


@router.post("/stop")
async def stop_autonomy():
    """Stop autonomy mode."""
    await redis_client.set(AUTONOMY_KEY, "off")
    await task_manager.set_global_stop(True)
    await asyncio.sleep(0.1)
    await task_manager.set_global_stop(False)
    return {"stopped": True}


@router.put("/focus")
async def update_focus(body: AutonomyStart):
    """Update the focus/direction for autonomy mode."""
    if body.focus:
        await redis_client.set(AUTONOMY_FOCUS_KEY, body.focus)
    return {"focus": body.focus}


async def _autonomy_loop(focus: str):
    """Background autonomy loop – finds learning tasks and executes them."""
    import json

    while True:
        # Check if still active
        state_raw = await redis_client.get(AUTONOMY_KEY)
        if not state_raw or state_raw.decode() != "on":
            break

        # Check cost limit
        if not await cost_tracker.check_limit(is_autonomy=True):
            await redis_client.set(AUTONOMY_KEY, "off")
            break

        # Create a self-directed learning task
        goal = f"Explore and learn something interesting or useful. Focus area: {focus or 'anything relevant to helping the user'}. Document findings in memory."
        state = task_manager.create(mode=TaskMode.AUTONOMY, goal=goal)
        await task_manager.save(state)

        async for _ in agent_loop.run_agent(state):
            # Check stop again during task
            state_raw = await redis_client.get(AUTONOMY_KEY)
            if not state_raw or state_raw.decode() != "on":
                await task_manager.request_stop(state.task_id)
                break

        # Wait before next task (avoid hammering API)
        await asyncio.sleep(60)
