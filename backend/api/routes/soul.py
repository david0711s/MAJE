"""MAJE – Soul & Memory Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from tools.memory_tools import get_soul, update_soul, save_memory, list_memory, delete_memory

router = APIRouter()


class SoulUpdate(BaseModel):
    text: str


class MemoryCreate(BaseModel):
    content: str
    tags: Optional[str] = ""


@router.get("/")
async def get_soul_endpoint():
    return {"soul": await get_soul()}


@router.put("/")
async def update_soul_endpoint(body: SoulUpdate):
    await update_soul(body.text)
    return {"updated": True}


@router.get("/memory")
async def list_memory_endpoint(search: Optional[str] = None, limit: int = 50):
    entries = await list_memory(search=search, limit=limit)
    return {"entries": entries, "count": len(entries)}


@router.post("/memory")
async def create_memory(body: MemoryCreate):
    result = await save_memory(content=body.content, tags=body.tags or "")
    return {"result": result}


@router.delete("/memory/{entry_id}")
async def delete_memory_endpoint(entry_id: str):
    deleted = await delete_memory(entry_id)
    if not deleted:
        raise HTTPException(404, "Memory entry not found")
    return {"deleted": True}
