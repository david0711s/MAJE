"""MAJE – UI Elements Routes (Für MAJE custom screen)"""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from storage.sqlite_db import db_execute
from tools.ui_tools import (
    create_ui_element,
    list_ui_elements,
    remove_ui_element,
    reorder_ui,
)

router = APIRouter()


class UIElementCreate(BaseModel):
    label: str
    action: str
    linked_script: str
    element_type: str = "button"
    config: str = "{}"


class ReorderRequest(BaseModel):
    order: List[str]


def _to_app_shape(el: dict) -> dict:
    """Map a DB row to the shape the app expects."""
    try:
        config = json.loads(el.get("config") or "{}")
    except Exception:
        config = {}
    return {
        "id": el.get("id"),
        "element_type": el.get("element_type", "button"),
        "title": el.get("label", ""),
        "description": el.get("action", ""),
        "payload": {
            "action": el.get("action"),
            "linked_script": el.get("linked_script"),
            "prompt": config.get("prompt") or el.get("action"),
            **config,
        },
        "order_index": el.get("order_index", 0),
        "created_at": el.get("created_at"),
        "task_id": el.get("task_id"),
    }


@router.get("")
@router.get("/")
async def get_elements_app():
    """App-compatible: returns a plain array of UI elements."""
    return [_to_app_shape(el) for el in await list_ui_elements()]


@router.delete("")
@router.delete("/")
async def clear_elements():
    """Remove all UI elements ('Alle Widgets entfernen')."""
    existing = await list_ui_elements()
    await db_execute("DELETE FROM ui_elements")
    return {"cleared": True, "removed": len(existing)}


@router.get("/elements")
async def get_elements():
    return {"elements": await list_ui_elements()}


@router.post("/elements")
async def add_element(body: UIElementCreate):
    result = await create_ui_element(
        label=body.label,
        action=body.action,
        linked_script=body.linked_script,
        element_type=body.element_type,
        config=body.config,
    )
    if result.startswith("ERROR"):
        raise HTTPException(400, result)
    return {"result": result}


@router.delete("/elements/{element_id}")
async def delete_element(element_id: str):
    result = await remove_ui_element(element_id)
    if result.startswith("ERROR"):
        raise HTTPException(404, result)
    return {"result": result}


@router.put("/elements/reorder")
async def reorder_elements(body: ReorderRequest):
    return {"result": await reorder_ui(body.order)}
