"""MAJE – Tasks Routes"""
from fastapi import APIRouter, HTTPException
from core.task_state import task_manager

router = APIRouter()

@router.get("/")
async def list_tasks():
    return await task_manager.list_tasks()

@router.get("/{task_id}")
async def get_task(task_id: str):
    state = await task_manager.load(task_id)
    if not state:
        raise HTTPException(404, "Task not found")
    return state.to_dict()

@router.delete("/{task_id}")
async def delete_task(task_id: str):
    await task_manager.delete(task_id)
    return {"deleted": True}
