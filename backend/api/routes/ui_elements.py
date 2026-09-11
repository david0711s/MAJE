"""MAJE – UI Elements Routes (Für MAJE custom screen)"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from tools.ui_tools import list_ui_elements, create_ui_element, remove_ui_element, reorder_ui

router = APIRouter()


class UIElementCreate(BaseModel):
    label: str
    action: str
    linked_script: str
    element_type: str = "button"
    config: str = "{}"


class ReorderRequest(BaseModel):
    order: List[str]


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
    result = await reorder_ui(body.order)
    return {"result": result}
