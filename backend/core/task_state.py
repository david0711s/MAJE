"""
MAJE – Task State Management
Persistent state per task, stored in Redis with SQLite backup.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from loguru import logger

from storage.redis_client import redis_client


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TaskMode(str, Enum):
    CHAT = "chat"
    AGENT = "agent"
    AUTONOMY = "autonomy"


class TaskState:
    """Represents the complete state of a single MAJE task."""

    def __init__(
        self,
        task_id: str,
        mode: TaskMode,
        goal: str,
        created_at: Optional[str] = None,
    ):
        self.task_id = task_id
        self.mode = mode
        self.goal = goal
        self.status = TaskStatus.PENDING
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.messages: list[dict] = []         # Full conversation history
        self.reasoning_log: list[dict] = []    # ReAct reasoning steps
        self.tool_calls: list[dict] = []       # Tool invocation history
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.active_provider: Optional[str] = None
        self.loop_count: int = 0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "reasoning_log": self.reasoning_log,
            "tool_calls": self.tool_calls,
            "result": self.result,
            "error": self.error,
            "active_provider": self.active_provider,
            "loop_count": self.loop_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskState":
        state = cls(task_id=d["task_id"], mode=d["mode"], goal=d["goal"], created_at=d["created_at"])
        state.status = d.get("status", TaskStatus.PENDING)
        state.updated_at = d.get("updated_at", state.created_at)
        state.messages = d.get("messages", [])
        state.reasoning_log = d.get("reasoning_log", [])
        state.tool_calls = d.get("tool_calls", [])
        state.result = d.get("result")
        state.error = d.get("error")
        state.active_provider = d.get("active_provider")
        state.loop_count = d.get("loop_count", 0)
        state.metadata = d.get("metadata", {})
        return state


class TaskManager:
    """Create, load, save, and list tasks."""

    TASK_KEY = "task:{task_id}"
    TASK_LIST_KEY = "tasks:list"
    STOP_FLAG_KEY = "stop:{task_id}"
    GLOBAL_STOP_KEY = "global:stop"

    def create(self, mode: TaskMode, goal: str) -> TaskState:
        task_id = str(uuid.uuid4())
        return TaskState(task_id=task_id, mode=mode, goal=goal)

    async def save(self, state: TaskState):
        state.updated_at = datetime.utcnow().isoformat()
        key = self.TASK_KEY.format(task_id=state.task_id)
        await redis_client.set(key, json.dumps(state.to_dict()), ex=86400 * 30)
        # Add to list
        await redis_client.sadd(self.TASK_LIST_KEY, state.task_id)

    async def load(self, task_id: str) -> Optional[TaskState]:
        key = self.TASK_KEY.format(task_id=task_id)
        raw = await redis_client.get(key)
        if not raw:
            return None
        return TaskState.from_dict(json.loads(raw))

    async def list_tasks(self, limit: int = 50) -> list[dict]:
        ids = await redis_client.smembers(self.TASK_LIST_KEY)
        tasks = []
        for tid in list(ids)[:limit]:
            tid_str = tid.decode() if isinstance(tid, bytes) else tid
            state = await self.load(tid_str)
            if state:
                # Return summary (no full message history)
                d = state.to_dict()
                d.pop("messages", None)
                d.pop("reasoning_log", None)
                tasks.append(d)
        return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)

    async def delete(self, task_id: str):
        key = self.TASK_KEY.format(task_id=task_id)
        await redis_client.delete(key)
        await redis_client.srem(self.TASK_LIST_KEY, task_id)

    # ── Stop signals ─────────────────────────────────────────────────────────

    async def request_stop(self, task_id: str):
        """Signal a specific task to stop."""
        key = self.STOP_FLAG_KEY.format(task_id=task_id)
        await redis_client.set(key, "1", ex=3600)
        logger.warning(f"🛑 Stop signal sent for task {task_id}")

    async def check_stop(self, task_id: str) -> bool:
        """Returns True if task should stop."""
        key = self.STOP_FLAG_KEY.format(task_id=task_id)
        flag = await redis_client.get(key)
        global_flag = await redis_client.get(self.GLOBAL_STOP_KEY)
        return bool(flag or global_flag)

    async def clear_stop(self, task_id: str):
        key = self.STOP_FLAG_KEY.format(task_id=task_id)
        await redis_client.delete(key)

    async def set_global_stop(self, value: bool):
        if value:
            await redis_client.set(self.GLOBAL_STOP_KEY, "1")
        else:
            await redis_client.delete(self.GLOBAL_STOP_KEY)


# Singleton
task_manager = TaskManager()
