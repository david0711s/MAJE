"""MAJE – Soul & Memory Routes"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tools.memory_tools import (
    delete_memory,
    list_memory,
    save_memory,
)
from tools.soul_store import get_soul_structured, get_soul_text, update_soul_structured, update_soul_text

router = APIRouter()


class SoulUpdate(BaseModel):
    # Structured (app) fields – all optional
    name: Optional[str] = None
    persona: Optional[str] = None
    tone: Optional[str] = None
    core_values: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
    # Legacy raw text field (agent tool / backwards compatibility)
    text: Optional[str] = None


class MemoryCreate(BaseModel):
    content: str
    tags: Optional[str] = ""


@router.get("/")
async def get_soul_endpoint():
    return await get_soul_structured()


@router.put("/")
async def update_soul_endpoint(body: SoulUpdate):
    if body.text is not None and all(
        v is None for v in (body.name, body.persona, body.tone, body.core_values, body.custom_instructions)
    ):
        await update_soul_text(body.text)
    else:
        await update_soul_structured(body.model_dump(exclude_none=True))
    return {"updated": True, "soul": await get_soul_structured()}


@router.post("/")
async def update_soul_post(body: SoulUpdate):
    """App uses POST for saving the structured soul."""
    return await update_soul_endpoint(body)


@router.get("/raw")
async def get_soul_raw_endpoint():
    return {"soul": get_soul_text()}


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
    if not await delete_memory(entry_id):
        raise HTTPException(404, "Memory entry not found")
    return {"deleted": True}
