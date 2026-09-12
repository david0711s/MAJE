"""
MAJE – Cost Tracker
Tracks token usage and costs per provider per day.
Stores in Redis when available, with an in-memory fallback so it always works
(e.g. in unit tests or when Redis is temporarily down).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Optional

from loguru import logger

from config.api_keys import COST_SETTINGS, API_PROVIDERS


# USD per 1k tokens (input, output) – fallback when a model isn't in API_PROVIDERS
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gemini": (0.0, 0.0),
    "llama-3.3-70b": (0.0, 0.0),
    "deepseek": (0.00027, 0.001),
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-3-5": (0.0008, 0.004),
    "mistral": (0.0002, 0.0006),
    "llama": (0.00088, 0.00088),
}


def _price_for(model: str) -> tuple[float, float]:
    """Resolve (usd_per_1k_in, usd_per_1k_out) for a model name."""
    m = (model or "").lower()
    for provider in API_PROVIDERS:
        if provider.get("model") and provider["model"].lower() in m:
            return (
                float(provider.get("cost_per_1k_input_tokens", 0.0)),
                float(provider.get("cost_per_1k_output_tokens", 0.0)),
            )
    for key, price in MODEL_PRICES.items():
        if key in m:
            return price
    return (0.0, 0.0)


def _provider_id_for_model(model: str) -> Optional[str]:
    m = (model or "").lower()
    for provider in API_PROVIDERS:
        if provider.get("model") and provider["model"].lower() in m:
            return provider["provider_id"]
    return None


class CostTracker:
    def __init__(self):
        self._redis = None  # Injected after Redis connects
        self._mem: dict = {}  # in-memory fallback store

    def _set_redis(self, redis):
        self._redis = redis

    def _today_key(self, provider_id: str) -> str:
        return f"costs:{date.today().isoformat()}:{provider_id}"

    def _total_key(self) -> str:
        return f"costs:{date.today().isoformat()}:__total__"

    def _rate(self) -> float:
        return float(COST_SETTINGS.get("eur_usd_rate", 1.08)) or 1.08

    def calculate_cost(self, model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> float:
        """Return the cost for a single call in EUR."""
        p_in, p_out = _price_for(model)
        cost_usd = (prompt_tokens / 1000.0) * p_in + (completion_tokens / 1000.0) * p_out
        return cost_usd / self._rate()

    async def record_usage(self, model: str, prompt_tokens: int = 0, completion_tokens: int = 0,
                           task_id: Optional[str] = None, provider_id: Optional[str] = None) -> float:
        """Record usage for a model. Returns the cost in EUR."""
        p_in, p_out = _price_for(model)
        pid = provider_id or _provider_id_for_model(model) or "unknown"
        await self.record(
            provider_id=pid,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_per_1k_in=p_in,
            cost_per_1k_out=p_out,
            task_id=task_id,
        )
        return self.calculate_cost(model, prompt_tokens, completion_tokens)

    async def record(
        self,
        provider_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_in: float,
        cost_per_1k_out: float,
        task_id: Optional[str] = None,
    ):
        """Record token usage and cost for a single API call."""
        cost_usd = (input_tokens / 1000) * cost_per_1k_in + (output_tokens / 1000) * cost_per_1k_out
        cost_eur = cost_usd / self._rate()

        key = self._today_key(provider_id)
        existing = await self._load(key) or {
            "provider_id": provider_id, "requests": 0,
            "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_eur": 0.0,
        }
        existing["requests"] += 1
        existing["input_tokens"] += input_tokens
        existing["output_tokens"] += output_tokens
        existing["cost_usd"] += cost_usd
        existing["cost_eur"] += cost_eur
        await self._save(key, existing)

        total = await self._load(self._total_key()) or {"cost_usd": 0.0, "cost_eur": 0.0, "requests": 0}
        total["cost_usd"] += cost_usd
        total["cost_eur"] += cost_eur
        total["requests"] += 1
        await self._save(self._total_key(), total)
        logger.debug(f"Cost recorded: {provider_id} ${cost_usd:.6f} (€{cost_eur:.6f})")
    async def get_today_total_eur(self) -> float:
        total = await self._load(self._total_key())
        return float(total.get("cost_eur", 0.0)) if total else 0.0

    async def get_today_costs(self) -> dict:
        """App-friendly summary of today's costs."""
        total = await self._load(self._total_key()) or {}
        breakdown = await self.get_daily_breakdown()
        prompt_tokens = sum(int(b.get("input_tokens", 0)) for b in breakdown)
        completion_tokens = sum(int(b.get("output_tokens", 0)) for b in breakdown)
        limit = float(COST_SETTINGS.get("daily_limit_eur", 2.0))
        return {
            "total_eur": round(float(total.get("cost_eur", 0.0)), 6),
            "limit_eur": limit,
            "daily_limit_eur": limit,
            "requests": int(total.get("requests", 0)),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "by_model": [
                {
                    "model": b.get("provider_id", "unknown"),
                    "cost_eur": round(float(b.get("cost_eur", 0.0)), 6),
                    "tokens": int(b.get("input_tokens", 0)) + int(b.get("output_tokens", 0)),
                }
                for b in breakdown
            ],
            "breakdown": breakdown,
        }

    async def check_limit(self, is_autonomy: bool = False) -> bool:
        """Returns True if still within limit, False if limit exceeded."""
        total = await self.get_today_total_eur()
        limit_key = "autonomy_mode_daily_limit_eur" if is_autonomy else "daily_limit_eur"
        limit = COST_SETTINGS.get(limit_key, 2.0)
        if limit <= 0:
            return True  # No limit set
        return total < limit

    async def get_daily_breakdown(self, target_date: Optional[str] = None) -> list[dict]:
        """Get cost breakdown by provider for a given date (YYYY-MM-DD)."""
        d = target_date or date.today().isoformat()
        prefix = f"costs:{d}:"
        result: list[dict] = []
        if self._redis is not None:
            try:
                keys = await self._redis.keys(f"{prefix}*")
                for k in keys:
                    kk = k.decode() if isinstance(k, bytes) else k
                    if "__total__" in kk:
                        continue
                    raw = await self._redis.get(kk)
                    if raw:
                        result.append(json.loads(raw))
                return result
            except Exception as e:  # pragma: no cover - fall back to memory
                logger.warning(f"CostTracker Redis read failed: {e}")
        for k, v in self._mem.items():
            if k.startswith(prefix) and "__total__" not in k:
                result.append(v)
        return result

    async def get_monthly_totals(self) -> list[dict]:
        """Get daily totals for the last 30 days."""
        totals = []
        today = date.today()
        for i in range(30):
            d = (today - timedelta(days=i)).isoformat()
            entry = await self._load(f"costs:{d}:__total__") or {"cost_usd": 0.0, "cost_eur": 0.0, "requests": 0}
            entry = dict(entry)
            entry["date"] = d
            totals.append(entry)
        return list(reversed(totals))

    # ── Storage abstraction (Redis with in-memory fallback) ───────────────────

    async def _load(self, key: str) -> Optional[dict]:
        if self._redis is not None:
            try:
                raw = await self._redis.get(key)
                return json.loads(raw) if raw else None
            except Exception as e:  # pragma: no cover
                logger.warning(f"CostTracker Redis get failed: {e}")
        return self._mem.get(key)

    async def _save(self, key: str, value: dict):
        self._mem[key] = value
        if self._redis is not None:
            try:
                await self._redis.set(key, json.dumps(value), ex=86400 * 32)
            except Exception as e:  # pragma: no cover
                logger.warning(f"CostTracker Redis set failed: {e}")


# Singleton
cost_tracker = CostTracker()

