"""MAJE – Tasks Routes"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.task_state import task_manager

router = APIRouter()


def _to_app_task(d: dict) -> dict:
    """Fügt die Feldnamen hinzu, die die App erwartet (id/description/…)."""
    result = dict(d)
    result["id"] = d.get("task_id")
    result["description"] = d.get("goal")
    meta = d.get("metadata") or {}
    result["total_cost_eur"] = meta.get("cost_eur", 0.0)
    result["steps_count"] = d.get("loop_count", 0)
    if "reasoning_log" in d:
        result["steps"] = d.get("reasoning_log") or []
    return result


@router.get("/")
async def list_tasks():
    tasks = await task_manager.list_tasks()
    return [_to_app_task(t) for t in tasks]


@router.get("/{task_id}")
async def get_task(task_id: str):
    state = await task_manager.load(task_id)
    if not state:
        raise HTTPException(404, "Task not found")
    return _to_app_task(state.to_dict())


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    await task_manager.delete(task_id)
    return {"deleted": True}

