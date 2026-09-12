"""
MAJE – Chat & Agent WebSocket Route
POST   /chat/message          → single chat message (Chat Mode)
POST   /chat/agent            → start agent/autonomy task, returns task_id
WS     /chat/ws?token=<JWT>   → live agent updates (auth REQUIRED)
DELETE /chat/stop/{task_id}   → stop a running task
DELETE /chat/stop-all         → global emergency stop
"""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.agent_loop import agent_loop
from core.cost_tracker import cost_tracker
from core.task_state import TaskMode, task_manager
from api.middleware.auth import verify_ws_token
from config.api_keys import API_PROVIDERS

router = APIRouter()

# Active WebSocket subscribers: task_id → set of WebSockets
_subscribers: dict[str, set[WebSocket]] = {}


async def _broadcast(task_id: str, payload: dict):
    """Send a live event to every WebSocket subscribed to a task."""
    for ws in list(_subscribers.get(task_id, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            _subscribers.get(task_id, set()).discard(ws)


class ChatRequest(BaseModel):
    message: str
    task_id: Optional[str] = None


class AgentRequest(BaseModel):
    goal: Optional[str] = None
    task: Optional[str] = None  # alias accepted from the app
    mode: str = "agent"


# ── HTTP: Chat Mode ───────────────────────────────────────────────────────────

@router.post("/message")
async def chat_message(req: ChatRequest):
    """Send a chat message and get a response (no tools)."""
    if not await cost_tracker.check_limit():
        raise HTTPException(402, "Daily cost limit reached. Increase it in Settings or try again tomorrow.")

    if req.task_id:
        state = await task_manager.load(req.task_id)
        if not state:
            raise HTTPException(404, "Task not found")
    else:
        state = task_manager.create(mode=TaskMode.CHAT, goal="Chat session")
        await task_manager.save(state)

    reply = await agent_loop.run_chat(state, req.message)

    active = next(
        (p["name"] for p in API_PROVIDERS if p["provider_id"] == state.active_provider),
        state.active_provider or "Unknown",
    )

    return {
        "task_id": state.task_id,
        "reply": reply,
        "model_used": state.metadata.get("model", active),
        "active_provider": active,
        "cost_eur": state.metadata.get("cost_eur", 0.0),
    }


# ── HTTP: Start Agent Task ────────────────────────────────────────────────────

@router.post("/agent")
async def start_agent(req: AgentRequest):
    """Start an agent or autonomy task. Returns task_id immediately."""
    goal = (req.goal or req.task or "").strip()
    if not goal:
        raise HTTPException(400, "Missing 'goal' (or 'task').")

    try:
        mode = TaskMode(req.mode)
    except ValueError:
        raise HTTPException(400, f"Invalid mode: {req.mode}. Use: chat, agent, autonomy")

    if not await cost_tracker.check_limit(is_autonomy=(mode == TaskMode.AUTONOMY)):
        raise HTTPException(402, "Daily cost limit reached. Autonomy/agent task not started.")

    state = task_manager.create(mode=mode, goal=goal)
    await task_manager.save(state)

    async def run():
        async def emit(payload: dict):
            await _broadcast(state.task_id, payload)

        try:
            await agent_loop.run_agent(state, emit=emit)
        except Exception as e:  # pragma: no cover
            await task_manager.request_stop(state.task_id)
            await _broadcast(state.task_id, {"type": "failed", "task_id": state.task_id, "error": str(e)})

    asyncio.create_task(run())
    return {"task_id": state.task_id, "status": "started", "mode": req.mode}


# ── HTTP: Stop Task ───────────────────────────────────────────────────────────

@router.delete("/stop/{task_id}")
async def stop_task(task_id: str):
    await task_manager.request_stop(task_id)
    return {"task_id": task_id, "stopped": True}


@router.delete("/stop-all")
async def stop_all():
    await task_manager.set_global_stop(True)
    return {"global_stop": True}


@router.post("/resume-all")
async def resume_all():
    await task_manager.set_global_stop(False)
    return {"global_stop": False}


# ── WebSocket: Live Updates ───────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: Optional[str] = None):
    """WebSocket for live agent updates. Requires a valid JWT (?token=...)."""
    if not token or not verify_ws_token(token):
        await ws.close(code=4001)
        return

    await ws.accept()
    my_subs: set[str] = set()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            action = msg.get("action")

            if action == "subscribe":
                task_id = msg.get("task_id")
                if task_id:
                    _subscribers.setdefault(task_id, set()).add(ws)
                    my_subs.add(task_id)
                    await ws.send_json({"type": "subscribed", "task_id": task_id})

            elif action == "stop":
                task_id = msg.get("task_id")
                if task_id:
                    await task_manager.request_stop(task_id)
                    await ws.send_json({"type": "stop_sent", "task_id": task_id})

            elif action == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        for task_id in my_subs:
            _subscribers.get(task_id, set()).discard(ws)
