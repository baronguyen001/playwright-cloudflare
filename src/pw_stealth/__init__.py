"""Playwright stealth defaults for authorized testing."""

from .fingerprint import (
    STEALTH_FINGERPRINT,
    UA_POOL,
    VIEWPORTS,
    Fingerprint,
    FingerprintProfile,
    fingerprint_context_options,
    fingerprint_init_script,
    random_fingerprint,
)
from .presets import (
    is_internally_consistent,
    load_preset,
    preset_engine,
    preset_names,
)
from .stealth import (
    STEALTH_ARGS,
    STEALTH_INIT_JS,
    apply_stealth,
    stealth_browser,
    stealth_context,
)
from .sync_stealth import apply_stealth_sync, stealth_browser_sync, stealth_context_sync

__version__ = "0.3.0"

__all__ = [
    "Fingerprint",
    "FingerprintProfile",
    "STEALTH_ARGS",
    "STEALTH_FINGERPRINT",
    "STEALTH_INIT_JS",
    "UA_POOL",
    "VIEWPORTS",
    "__version__",
    "apply_stealth",
    "apply_stealth_sync",
    "fingerprint_context_options",
    "fingerprint_init_script",
    "is_internally_consistent",
    "load_preset",
    "preset_engine",
    "preset_names",
    "random_fingerprint",
    "stealth_browser",
    "stealth_browser_sync",
    "stealth_context",
    "stealth_context_sync",
]
