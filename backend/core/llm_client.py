"""
MAJE – Multi-API Fallback LLM Client
Reads API_PROVIDERS from config/api_keys.py and iterates the fallback chain.
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
import time
from typing import AsyncIterator, Optional
from dataclasses import dataclass, field

import google.generativeai as genai
from groq import AsyncGroq
from openai import AsyncOpenAI
import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.api_keys import API_PROVIDERS, INTERNAL
from .cost_tracker import cost_tracker


@dataclass
class LLMResponse:
    content: str
    provider_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class ProviderState:
    """Runtime state for a single provider (key rotation, daily counter)."""
    provider_id: str
    key_index: int = 0
    requests_today: int = 0
    last_reset: float = field(default_factory=time.time)

    def next_key(self, keys: list[str]) -> Optional[str]:
        if not keys:
            return None
        key = keys[self.key_index % len(keys)]
        self.key_index = (self.key_index + 1) % len(keys)
        return key

    def check_and_reset_daily(self):
        now = time.time()
        if now - self.last_reset > 86400:
            self.requests_today = 0
            self.last_reset = now


class LLMClient:
    """
    Iterates the API_PROVIDERS fallback chain.
    Skips: disabled providers, providers without keys, providers over daily limit.
    """

    def __init__(self):
        self._states: dict[str, ProviderState] = {
            p["provider_id"]: ProviderState(p["provider_id"])
            for p in API_PROVIDERS
        }

    def _get_active_providers(self) -> list[dict]:
        active = []
        for p in API_PROVIDERS:
            if not p.get("enabled", True):
                continue
            keys = [k for k in p.get("keys", []) if k and not k.startswith("DEIN_")]
            if not keys:
                logger.debug(f"Skipping {p['name']}: no keys configured")
                continue
            state = self._states[p["provider_id"]]
            state.check_and_reset_daily()
            rpd = p.get("rpd_limit", 0)
            if rpd > 0 and state.requests_today >= rpd:
                logger.warning(f"Skipping {p['name']}: daily limit {rpd} reached")
                continue
            active.append(p)
        return active

    async def complete(
        self,
        messages: list[dict],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = INTERNAL["max_tokens_per_request"],
    ) -> LLMResponse:
        """Try each provider in order. Returns first successful response."""
        providers = self._get_active_providers()
        if not providers:
            raise RuntimeError("No LLM providers available. Please configure API keys.")

        last_error = None
        for provider in providers:
            try:
                resp = await self._call_provider(provider, messages, system_prompt, temperature, max_tokens)
                state = self._states[provider["provider_id"]]
                state.requests_today += 1
                await cost_tracker.record(
                    provider_id=provider["provider_id"],
                    input_tokens=resp.input_tokens,
                    output_tokens=resp.output_tokens,
                    cost_per_1k_in=provider.get("cost_per_1k_input_tokens", 0),
                    cost_per_1k_out=provider.get("cost_per_1k_output_tokens", 0),
                )
                logger.info(f"✅ {provider['name']} responded ({resp.input_tokens}in/{resp.output_tokens}out tokens)")
                return resp
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️  {provider['name']} failed: {e} – trying next provider")
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def stream(
        self,
        messages: list[dict],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = INTERNAL["max_tokens_per_request"],
    ) -> AsyncIterator[str]:
        """Streaming version – yields text chunks."""
        providers = self._get_active_providers()
        if not providers:
            raise RuntimeError("No LLM providers available.")

        for provider in providers:
            try:
                async for chunk in self._stream_provider(provider, messages, system_prompt, temperature, max_tokens):
                    yield chunk
                state = self._states[provider["provider_id"]]
                state.requests_today += 1
                return
            except Exception as e:
                logger.warning(f"⚠️  Streaming failed for {provider['name']}: {e}")
                continue

        raise RuntimeError("All streaming providers failed.")

    # ── Provider-specific callers ─────────────────────────────────────────────

    async def _call_provider(
        self, p: dict, messages: list[dict], system_prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        pid = p["provider_id"]
        state = self._states[pid]
        keys = [k for k in p.get("keys", []) if k and not k.startswith("DEIN_")]
        key = state.next_key(keys)

        if pid == "gemini":
            return await self._call_gemini(key, p["model"], messages, system_prompt, temperature, max_tokens)
        elif pid in ("groq", "deepseek", "openai", "mistral", "together"):
            return await self._call_openai_compat(key, p["model"], p.get("base_url"), messages, system_prompt, temperature, max_tokens, pid)
        elif pid == "anthropic":
            return await self._call_anthropic(key, p["model"], messages, system_prompt, temperature, max_tokens)
        else:
            raise NotImplementedError(f"Unknown provider_id: {pid}")

    async def _call_gemini(self, key: str, model: str, messages: list[dict], system_prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        genai.configure(api_key=key)
        client = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt or None,
            generation_config=genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
        )
        # Convert to Gemini format
        history = []
        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        chat = client.start_chat(history=history)
        response = await asyncio.to_thread(chat.send_message, messages[-1]["content"])
        text = response.text
        usage = response.usage_metadata
        return LLMResponse(
            content=text,
            provider_id="gemini",
            model=model,
            input_tokens=getattr(usage, "prompt_token_count", 0),
            output_tokens=getattr(usage, "candidates_token_count", 0),
        )

    async def _call_openai_compat(self, key: str, model: str, base_url: Optional[str], messages: list[dict], system_prompt: str, temperature: float, max_tokens: int, pid: str) -> LLMResponse:
        kwargs = {"api_key": key, "timeout": INTERNAL["request_timeout_sec"]}
        if base_url:
            kwargs["base_url"] = base_url
        client = AsyncOpenAI(**kwargs)
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        response = await client.chat.completions.create(
            model=model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content,
            provider_id=pid,
            model=model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

    async def _call_anthropic(self, key: str, model: str, messages: list[dict], system_prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        client = anthropic.AsyncAnthropic(api_key=key)
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt or anthropic.NOT_GIVEN,
            messages=messages,
            temperature=temperature,
        )
        return LLMResponse(
            content=response.content[0].text,
            provider_id="anthropic",
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    async def _stream_provider(self, p: dict, messages: list[dict], system_prompt: str, temperature: float, max_tokens: int) -> AsyncIterator[str]:
        pid = p["provider_id"]
        state = self._states[pid]
        keys = [k for k in p.get("keys", []) if k and not k.startswith("DEIN_")]
        key = state.next_key(keys)

        if pid == "gemini":
            # Gemini streaming
            genai.configure(api_key=key)
            client = genai.GenerativeModel(model_name=p["model"], system_instruction=system_prompt or None)
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[:-1]]
            chat = client.start_chat(history=history)
            response = await asyncio.to_thread(lambda: chat.send_message(messages[-1]["content"], stream=True))
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        else:
            # OpenAI-compat streaming
            kwargs = {"api_key": key, "timeout": INTERNAL["request_timeout_sec"]}
            if p.get("base_url"):
                kwargs["base_url"] = p["base_url"]
            client = AsyncOpenAI(**kwargs)
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            async with client.chat.completions.stream(model=p["model"], messages=full_messages, temperature=temperature, max_tokens=max_tokens) as stream:
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yield delta


# Singleton
llm_client = LLMClient()
