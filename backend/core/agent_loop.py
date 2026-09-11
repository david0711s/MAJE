"""
MAJE – ReAct Agent Loop
Reasoning → Action (Tool) → Observation → repeat until done / stopped.
"""
from __future__ import annotations

import json
import asyncio
from datetime import datetime
from typing import AsyncIterator, Optional, Callable

from loguru import logger

from .llm_client import llm_client
from .cost_tracker import cost_tracker
from .task_state import TaskState, TaskStatus, task_manager
from tools import TOOL_REGISTRY

SYSTEM_PROMPT_AGENT = """You are MAJE, a powerful personal AI agent. You operate in Agent Mode.

Your capabilities (tools):
{tool_descriptions}

Instructions:
- Think step-by-step before acting (Reasoning phase).
- Use tools to accomplish the goal.
- After each tool result, reason again (Observation phase).
- When the goal is achieved, reply with: TASK_COMPLETE: <summary>
- If you encounter an unrecoverable error: TASK_FAILED: <reason>
- Never fabricate tool results. Always use real tool calls.
- You have access to a custom UI area ("Für MAJE") where you can add buttons/widgets. Only add elements that are genuinely useful and linked to a real script.
- You have persistent memory. Use save_memory() for important long-term information.

Format for tool calls (JSON in your response):
```json
{{"tool": "tool_name", "args": {{"param1": "value1"}}}}
```
"""

SYSTEM_PROMPT_CHAT = """You are MAJE, a personal AI assistant. You are in Chat Mode.
You do NOT have access to tools in this mode. Have a helpful conversation.
Be concise, precise, and friendly. You know the user personally.
"""

MAX_LOOP_ITERATIONS = 30


class AgentLoop:
    def __init__(self):
        self._ws_callback: Optional[Callable] = None

    def set_ws_callback(self, cb: Callable):
        """Inject WebSocket send function for live updates."""
        self._ws_callback = cb

    async def _emit(self, event_type: str, data: dict, task_id: str):
        """Send live update via WebSocket if callback is set."""
        if self._ws_callback:
            try:
                await self._ws_callback({"type": event_type, "task_id": task_id, **data})
            except Exception:
                pass

    async def run_chat(self, state: TaskState, user_message: str) -> str:
        """Simple chat mode – no tools, no loop."""
        state.messages.append({"role": "user", "content": user_message})
        response = await llm_client.complete(
            messages=state.messages,
            system_prompt=SYSTEM_PROMPT_CHAT,
            temperature=0.7,
        )
        state.messages.append({"role": "assistant", "content": response.content})
        state.active_provider = response.provider_id
        await task_manager.save(state)
        return response.content

    async def run_agent(self, state: TaskState) -> AsyncIterator[dict]:
        """
        Full ReAct Agent Loop. Yields reasoning/action/observation events.
        Call this in a background task and stream via WebSocket.
        """
        state.status = TaskStatus.RUNNING
        await task_manager.save(state)

        # Build tool descriptions for system prompt
        tool_desc = "\n".join(
            f"- {name}: {info['description']}"
            for name, info in TOOL_REGISTRY.items()
        )
        system_prompt = SYSTEM_PROMPT_AGENT.format(tool_descriptions=tool_desc)

        # Load memory context
        from tools.memory_tools import load_relevant_memory
        memory_ctx = await load_relevant_memory(state.goal)
        if memory_ctx:
            system_prompt += f"\n\nYour relevant memories:\n{memory_ctx}"

        # Add goal as first user message if not already set
        if not state.messages:
            state.messages.append({"role": "user", "content": state.goal})

        await self._emit("status", {"status": "running", "message": "Agent loop started"}, state.task_id)

        while state.loop_count < MAX_LOOP_ITERATIONS:
            # Check stop signal
            if await task_manager.check_stop(state.task_id):
                state.status = TaskStatus.STOPPED
                state.result = "Task stopped by user."
                await task_manager.save(state)
                await self._emit("stopped", {"message": "Task stopped by user."}, state.task_id)
                return

            # Check cost limit
            if not await cost_tracker.check_limit(is_autonomy=(state.mode == "autonomy")):
                state.status = TaskStatus.PAUSED
                state.error = "Daily cost limit reached. Task paused."
                await task_manager.save(state)
                await self._emit("cost_limit", {"message": "Daily cost limit reached."}, state.task_id)
                return

            state.loop_count += 1
            logger.info(f"Agent loop iteration {state.loop_count} for task {state.task_id}")

            # ── Reasoning Phase ──────────────────────────────────────────────
            reasoning_step = {
                "step": state.loop_count,
                "phase": "reasoning",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self._emit("reasoning_start", reasoning_step, state.task_id)

            try:
                response = await llm_client.complete(
                    messages=state.messages,
                    system_prompt=system_prompt,
                    temperature=0.3,
                )
                state.active_provider = response.provider_id
            except Exception as e:
                state.status = TaskStatus.FAILED
                state.error = str(e)
                await task_manager.save(state)
                await self._emit("error", {"error": str(e)}, state.task_id)
                return

            reasoning_text = response.content
            reasoning_step["content"] = reasoning_text
            reasoning_step["provider"] = response.provider_id
            state.reasoning_log.append(reasoning_step)
            state.messages.append({"role": "assistant", "content": reasoning_text})
            await self._emit("reasoning", reasoning_step, state.task_id)

            # ── Check for DONE / FAILED ──────────────────────────────────────
            if "TASK_COMPLETE:" in reasoning_text:
                summary = reasoning_text.split("TASK_COMPLETE:", 1)[1].strip()
                state.status = TaskStatus.COMPLETED
                state.result = summary
                await task_manager.save(state)
                await self._emit("completed", {"result": summary}, state.task_id)
                return

            if "TASK_FAILED:" in reasoning_text:
                reason = reasoning_text.split("TASK_FAILED:", 1)[1].strip()
                state.status = TaskStatus.FAILED
                state.error = reason
                await task_manager.save(state)
                await self._emit("failed", {"error": reason}, state.task_id)
                return

            # ── Action Phase: parse tool call ─────────────────────────────────
            tool_call = self._parse_tool_call(reasoning_text)
            if not tool_call:
                # No tool call → model is just thinking, add dummy observation
                state.messages.append({"role": "user", "content": "Continue. If done, use TASK_COMPLETE:. If need a tool, format the call as JSON."})
                await task_manager.save(state)
                continue

            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {})

            action_step = {
                "step": state.loop_count,
                "phase": "action",
                "tool": tool_name,
                "args": tool_args,
                "timestamp": datetime.utcnow().isoformat(),
            }
            state.tool_calls.append(action_step)
            await self._emit("action", action_step, state.task_id)

            # ── Execute Tool ─────────────────────────────────────────────────
            tool_fn = TOOL_REGISTRY.get(tool_name, {}).get("fn")
            if not tool_fn:
                observation = f"ERROR: Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"
            else:
                try:
                    result = await tool_fn(task_id=state.task_id, **tool_args)
                    observation = str(result)
                except Exception as e:
                    observation = f"ERROR executing {tool_name}: {e}"
                    logger.error(f"Tool error: {e}")

            obs_step = {
                "step": state.loop_count,
                "phase": "observation",
                "tool": tool_name,
                "result": observation[:2000],  # Truncate for display
                "timestamp": datetime.utcnow().isoformat(),
            }
            state.reasoning_log.append(obs_step)
            state.messages.append({"role": "user", "content": f"Tool result for {tool_name}:\n{observation}"})
            await self._emit("observation", obs_step, state.task_id)
            await task_manager.save(state)

        # Max iterations reached
        state.status = TaskStatus.FAILED
        state.error = f"Max iterations ({MAX_LOOP_ITERATIONS}) reached without completion."
        await task_manager.save(state)
        await self._emit("failed", {"error": state.error}, state.task_id)

    def _parse_tool_call(self, text: str) -> Optional[dict]:
        """Extract JSON tool call from model output."""
        import re
        # Look for ```json ... ``` blocks
        pattern = r"```json\s*(\{.*?\})\s*```"
        matches = re.findall(pattern, text, re.DOTALL)
        for m in matches:
            try:
                data = json.loads(m)
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                continue
        # Fallback: bare JSON object with "tool" key
        pattern2 = r'\{[^{}]*"tool"[^{}]*\}'
        matches2 = re.findall(pattern2, text, re.DOTALL)
        for m in matches2:
            try:
                data = json.loads(m)
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                continue
        return None


# Singleton
agent_loop = AgentLoop()
