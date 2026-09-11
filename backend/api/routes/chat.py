"""
MAJE – Chat & Agent WebSocket Route
POST /chat/message    → single chat message (Chat Mode)
POST /chat/agent      → start agent task (Agent Mode)
WS   /chat/ws         → WebSocket for live agent updates
DELETE /chat/stop/{task_id} → stop a running task
"""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from core.agent_loop import agent_loop
from core.task_state import TaskMode, task_manager
from api.middleware.auth import verify_ws_token
from config.api_keys import API_PROVIDERS

router = APIRouter()

# Active WebSocket connections: task_id → WebSocket
_ws_connections: dict[str, WebSocket] = {}


class ChatRequest(BaseModel):
    message: str
    task_id: Optional[str] = None


class AgentRequest(BaseModel):
    goal: str
    mode: str = "agent"


# ── HTTP: Chat Mode ───────────────────────────────────────────────────────────

@router.post("/message")
async def chat_message(req: ChatRequest):
    """Send a chat message and get a response (no tools)."""
    if req.task_id:
        state = await task_manager.load(req.task_id)
        if not state:
            raise HTTPException(404, "Task not found")
    else:
        state = task_manager.create(mode=TaskMode.CHAT, goal="Chat session")
        await task_manager.save(state)

    reply = await agent_loop.run_chat(state, req.message)

    # Get active provider name
    active = next(
        (p["name"] for p in API_PROVIDERS if p["provider_id"] == state.active_provider),
        state.active_provider or "Unknown"
    )

    return {
        "task_id": state.task_id,
        "reply": reply,
        "active_provider": active,
    }


# ── HTTP: Start Agent Task ────────────────────────────────────────────────────

@router.post("/agent")
async def start_agent(req: AgentRequest):
    """Start an agent or autonomy task. Returns task_id immediately."""
    try:
        mode = TaskMode(req.mode)
    except ValueError:
        raise HTTPException(400, f"Invalid mode: {req.mode}. Use: chat, agent, autonomy")

    state = task_manager.create(mode=mode, goal=req.goal)
    await task_manager.save(state)

    # Start agent loop in background
    async def run():
        send_fn = _ws_connections.get(state.task_id)
        if send_fn:
            agent_loop.set_ws_callback(lambda data: send_fn.send_json(data))
        async for _ in agent_loop.run_agent(state):
            pass

    asyncio.create_task(run())

    return {"task_id": state.task_id, "status": "started", "mode": req.mode}


# ── HTTP: Stop Task ───────────────────────────────────────────────────────────

@router.delete("/stop/{task_id}")
async def stop_task(task_id: str):
    """Send stop signal to a running task."""
    await task_manager.request_stop(task_id)
    return {"task_id": task_id, "stopped": True}


@router.delete("/stop-all")
async def stop_all():
    """Global emergency stop – halts all running tasks."""
    await task_manager.set_global_stop(True)
    return {"global_stop": True}


@router.post("/resume-all")
async def resume_all():
    """Clear global stop flag."""
    await task_manager.set_global_stop(False)
    return {"global_stop": False}


# ── WebSocket: Live Updates ───────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: Optional[str] = None):
    """
    WebSocket for live agent reasoning/action/observation updates.
    Query param: ?token=<JWT>
    """
    if token and not verify_ws_token(token):
        await ws.close(code=4001)
        return

    await ws.accept()

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            if action == "subscribe":
                task_id = msg.get("task_id")
                if task_id:
                    _ws_connections[task_id] = ws
                    # Set callback on agent loop
                    agent_loop.set_ws_callback(
                        lambda data, _ws=ws: _ws.send_json(data)
                    )
                    await ws.send_json({"type": "subscribed", "task_id": task_id})

            elif action == "stop":
                task_id = msg.get("task_id")
                if task_id:
                    await task_manager.request_stop(task_id)
                    await ws.send_json({"type": "stop_sent", "task_id": task_id})

            elif action == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        # Clean up subscriptions
        _ws_connections = {k: v for k, v in _ws_connections.items() if v != ws}
