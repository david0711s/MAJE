"""
MAJE – ReAct Agent Loop
Reasoning → Action (Tool) → Observation → repeat until done / stopped.
Emits live events through an injected ``emit`` coroutine (per task, not global).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Callable, Optional

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
- Self-teaching & Persistence: When you encounter a task requiring new capabilities or custom tools, you can write scripts (`write_and_run_script`, `write_file`) and install necessary packages (`pip_install`, `apt_install`). Save reusable tools and skills permanently with `save_module(name, code, description)` into /maje/skills/ so you can reuse them in future tasks. Check existing skills with `list_files('skills')`.

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

    def set_ws_callback(self, cb: Optional[Callable]):
        """Legacy global callback (kept for backwards compatibility)."""
        self._ws_callback = cb

    async def _emit(self, event_type: str, data: dict, task_id: str, emit: Optional[Callable] = None):
        """Send a live update through the per-task emitter (fallback: global callback)."""
        payload = {"type": event_type, "task_id": task_id, **data}
        target = emit or self._ws_callback
        if target:
            try:
                await target(payload)
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
        state.metadata["model"] = response.model
        cost = cost_tracker.calculate_cost(response.model, response.input_tokens, response.output_tokens)
        state.metadata["cost_eur"] = round(state.metadata.get("cost_eur", 0.0) + cost, 6)
        await task_manager.save(state)
        return response.content
    async def run_agent(self, state: TaskState, emit: Optional[Callable] = None) -> None:
        """Full ReAct Agent Loop. Emits reasoning/action/observation events via ``emit``."""
        state.status = TaskStatus.RUNNING
        await task_manager.save(state)

        tool_desc = "\n".join(
            f"- {name}: {info['description']}"
            for name, info in TOOL_REGISTRY.items()
        )
        system_prompt = SYSTEM_PROMPT_AGENT.format(tool_descriptions=tool_desc)

        from tools.memory_tools import load_relevant_memory
        memory_ctx = await load_relevant_memory(state.goal)
        if memory_ctx:
            system_prompt += f"\n\nYour relevant memories:\n{memory_ctx}"

        if not state.messages:
            state.messages.append({"role": "user", "content": state.goal})

        await self._emit("status", {"status": "running", "message": "Agent loop started"}, state.task_id, emit)

        while state.loop_count < MAX_LOOP_ITERATIONS:
            if await task_manager.check_stop(state.task_id):
                state.status = TaskStatus.STOPPED
                state.result = "Task stopped by user."
                await task_manager.save(state)
                await self._emit("stopped", {"result": state.result, "total_cost_eur": state.metadata.get("cost_eur", 0.0)}, state.task_id, emit)
                return

            if not await cost_tracker.check_limit(is_autonomy=(state.mode == "autonomy")):
                state.status = TaskStatus.PAUSED
                state.error = "Daily cost limit reached. Task paused."
                await task_manager.save(state)
                await self._emit("failed", {"error": state.error, "total_cost_eur": state.metadata.get("cost_eur", 0.0)}, state.task_id, emit)
                return

            state.loop_count += 1
            logger.info(f"Agent loop iteration {state.loop_count} for task {state.task_id}")

            reasoning_step = {
                "step": state.loop_count,
                "iteration": state.loop_count,
                "phase": "reasoning",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self._emit("reasoning_start", reasoning_step, state.task_id, emit)

            try:
                response = await llm_client.complete(
                    messages=state.messages,
                    system_prompt=system_prompt,
                    temperature=0.3,
                )
                state.active_provider = response.provider_id
                state.metadata["model"] = response.model
            except Exception as e:
                state.status = TaskStatus.FAILED
                state.error = str(e)
                await task_manager.save(state)
                await self._emit("failed", {"error": str(e), "total_cost_eur": state.metadata.get("cost_eur", 0.0)}, state.task_id, emit)
                return

            step_cost = cost_tracker.calculate_cost(response.model, response.input_tokens, response.output_tokens)
            state.metadata["cost_eur"] = round(state.metadata.get("cost_eur", 0.0) + step_cost, 6)

            reasoning_text = response.content
            reasoning_step["content"] = reasoning_text
            reasoning_step["thought"] = reasoning_text
            reasoning_step["provider"] = response.provider_id
            state.reasoning_log.append(reasoning_step)
            state.messages.append({"role": "assistant", "content": reasoning_text})
            await self._emit("reasoning", reasoning_step, state.task_id, emit)

            if "TASK_COMPLETE:" in reasoning_text:
                summary = reasoning_text.split("TASK_COMPLETE:", 1)[1].strip()
                state.status = TaskStatus.COMPLETED
                state.result = summary
                await task_manager.save(state)
                await self._emit("completed", {"result": summary, "total_cost_eur": state.metadata.get("cost_eur", 0.0)}, state.task_id, emit)
                return

            if "TASK_FAILED:" in reasoning_text:
                reason = reasoning_text.split("TASK_FAILED:", 1)[1].strip()
                state.status = TaskStatus.FAILED
                state.error = reason
                await task_manager.save(state)
                await self._emit("failed", {"error": reason, "total_cost_eur": state.metadata.get("cost_eur", 0.0)}, state.task_id, emit)
                return
            # ── Action Phase: parse tool call ─────────────────────────────────
            tool_call = self._parse_tool_call(reasoning_text)
            if not tool_call:
                state.messages.append({
                    "role": "user",
                    "content": "Continue. If done, use TASK_COMPLETE:. If you need a tool, format the call as JSON.",
                })
                await task_manager.save(state)
                continue

            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {}) or {}

            action_step = {
                "step": state.loop_count,
                "iteration": state.loop_count,
                "phase": "action",
                "tool": tool_name,
                "action": tool_name,
                "action_input": tool_args,
                "args": tool_args,
                "timestamp": datetime.utcnow().isoformat(),
            }
            state.tool_calls.append(action_step)
            await self._emit("action", action_step, state.task_id, emit)

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
                "iteration": state.loop_count,
                "phase": "observation",
                "tool": tool_name,
                "action": tool_name,
                "result": observation[:2000],
                "observation": observation[:2000],
                "timestamp": datetime.utcnow().isoformat(),
            }
            state.reasoning_log.append(obs_step)
            state.messages.append({"role": "user", "content": f"Tool result for {tool_name}:\n{observation}"})
            await self._emit("observation", obs_step, state.task_id, emit)
            await task_manager.save(state)

        # Max iterations reached
        state.status = TaskStatus.FAILED
        state.error = f"Max iterations ({MAX_LOOP_ITERATIONS}) reached without completion."
        await task_manager.save(state)
        await self._emit("failed", {"error": state.error, "total_cost_eur": state.metadata.get("cost_eur", 0.0)}, state.task_id, emit)

    def _parse_tool_call(self, text: str) -> Optional[dict]:
        """Extract a JSON tool call from the model output."""
        import re
        pattern = r"```json\s*(\{.*?\})\s*```"
        for m in re.findall(pattern, text, re.DOTALL):
            try:
                data = json.loads(m)
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                continue
        pattern2 = r'\{[^{}]*"tool"[^{}]*\}'
        for m in re.findall(pattern2, text, re.DOTALL):
            try:
                data = json.loads(m)
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                continue
        return None


# Singleton
agent_loop = AgentLoop()


