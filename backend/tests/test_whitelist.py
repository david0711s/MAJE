"""
MAJE – Whitelist Middleware & Verification Tests
"""
import pytest
import sys
from pathlib import Path

# Add backend and root directory to python path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.api.middleware.whitelist import verify_access


def test_whitelist_allows_when_disabled():
    config = {
        "active": False,
        "allowed_numbers": ["+491701234567"],
        "allowed_passcodes": ["secret123"]
    }
    # Should allow any sender if inactive
    allowed, reason = verify_access(sender="+499999999999", passcode=None, config=config)
    assert allowed is True
    assert reason == "whitelist_disabled"


def test_whitelist_allows_registered_number():
    config = {
        "active": True,
        "allowed_numbers": ["+491701234567"],
        "allowed_passcodes": ["secret123"]
    }
    allowed, reason = verify_access(sender="+491701234567", passcode=None, config=config)
    assert allowed is True
    assert reason == "allowed_number"


def test_whitelist_allows_registered_passcode():
    config = {
        "active": True,
        "allowed_numbers": ["+491701234567"],
        "allowed_passcodes": ["secret123"]
    }
    allowed, reason = verify_access(sender=None, passcode="secret123", config=config)
    assert allowed is True
    assert reason == "allowed_passcode"


def test_whitelist_blocks_unauthorized_sender():
    config = {
        "active": True,
        "allowed_numbers": ["+491701234567"],
        "allowed_passcodes": ["secret123"]
    }
    allowed, reason = verify_access(sender="+491510000000", passcode="wrong-code", config=config)
    assert allowed is False
    assert "access_denied" in reason
