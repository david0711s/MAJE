"""
MAJE – Cost Tracker Unit Tests
"""
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.core.cost_tracker import CostTracker


@pytest.mark.asyncio
async def test_calculate_cost():
    tracker = CostTracker()

    # Calculate cost for 1000 prompt tokens and 1000 completion tokens of gpt-4o
    cost = tracker.calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=1000)
    assert cost > 0.0
    # gpt-4o price: 2.50 / 1M prompt -> 0.0025, 10.00 / 1M completion -> 0.010 -> total ~0.0125 USD * EUR conversion
    assert cost < 0.05


@pytest.mark.asyncio
async def test_record_and_get_today_cost():
    tracker = CostTracker()
    # A paid model must produce a non-zero cost ...
    await tracker.record_usage("deepseek-chat", prompt_tokens=2000, completion_tokens=1000)

    today = await tracker.get_today_costs()
    assert "total_eur" in today
    assert today["total_eur"] > 0
    assert len(today.get("by_model", [])) > 0


@pytest.mark.asyncio
async def test_free_model_has_zero_cost():
    tracker = CostTracker()
    # ... while a free-tier model (Gemini) must not cost anything.
    cost = tracker.calculate_cost("gemini-2.5-flash", prompt_tokens=5000, completion_tokens=2000)
    assert cost == 0.0
