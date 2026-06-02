"""Playwright stealth defaults for authorized testing."""

from .fingerprint import STEALTH_FINGERPRINT, UA_POOL, VIEWPORTS, Fingerprint, random_fingerprint
from .stealth import STEALTH_ARGS, STEALTH_INIT_JS, apply_stealth, stealth_browser, stealth_context

__all__ = [
    "Fingerprint",
    "STEALTH_ARGS",
    "STEALTH_FINGERPRINT",
    "STEALTH_INIT_JS",
    "UA_POOL",
    "VIEWPORTS",
    "apply_stealth",
    "random_fingerprint",
    "stealth_browser",
    "stealth_context",
]
