"""
MAJE – Cost Tracker
Tracks token usage and costs per provider per day. Stores in Redis.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Optional

from loguru import logger

from config.api_keys import COST_SETTINGS


class CostTracker:
    def __init__(self):
        self._redis = None  # Injected after Redis connects

    def _set_redis(self, redis):
        self._redis = redis

    def _today_key(self, provider_id: str) -> str:
        return f"costs:{date.today().isoformat()}:{provider_id}"

    def _total_key(self) -> str:
        return f"costs:{date.today().isoformat()}:__total__"

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
        rate = COST_SETTINGS.get("eur_usd_rate", 1.08)
        cost_eur = cost_usd / rate

        if self._redis is None:
            logger.warning("CostTracker: Redis not connected, skipping record")
            return

        key = self._today_key(provider_id)
        existing_raw = await self._redis.get(key)
        existing = json.loads(existing_raw) if existing_raw else {
            "provider_id": provider_id,
            "requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "cost_eur": 0.0,
        }
        existing["requests"] += 1
        existing["input_tokens"] += input_tokens
        existing["output_tokens"] += output_tokens
        existing["cost_usd"] += cost_usd
        existing["cost_eur"] += cost_eur
        await self._redis.set(key, json.dumps(existing), ex=86400 * 32)

        # Update total
        total_key = self._total_key()
        total_raw = await self._redis.get(total_key)
        total = json.loads(total_raw) if total_raw else {"cost_usd": 0.0, "cost_eur": 0.0, "requests": 0}
        total["cost_usd"] += cost_usd
        total["cost_eur"] += cost_eur
        total["requests"] += 1
        await self._redis.set(total_key, json.dumps(total), ex=86400 * 32)

        logger.debug(f"Cost recorded: {provider_id} ${cost_usd:.6f} (€{cost_eur:.6f})")

    async def get_today_total_eur(self) -> float:
        if not self._redis:
            return 0.0
        raw = await self._redis.get(self._total_key())
        if not raw:
            return 0.0
        return json.loads(raw).get("cost_eur", 0.0)

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
        if not self._redis:
            return []
        d = target_date or date.today().isoformat()
        pattern = f"costs:{d}:*"
        keys = await self._redis.keys(pattern)
        result = []
        for k in keys:
            if b"__total__" in k:
                continue
            raw = await self._redis.get(k)
            if raw:
                result.append(json.loads(raw))
        return result

    async def get_monthly_totals(self) -> list[dict]:
        """Get daily totals for the last 30 days."""
        if not self._redis:
            return []
        from datetime import timedelta
        totals = []
        today = date.today()
        for i in range(30):
            d = (today - timedelta(days=i)).isoformat()
            key = f"costs:{d}:__total__"
            raw = await self._redis.get(key)
            entry = json.loads(raw) if raw else {"cost_usd": 0.0, "cost_eur": 0.0, "requests": 0}
            entry["date"] = d
            totals.append(entry)
        return list(reversed(totals))


# Singleton
cost_tracker = CostTracker()
