"""Small desktop fingerprint pool for Playwright contexts."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Fingerprint:
    user_agent: str
    viewport: dict
    locale: str
    timezone_id: str


UA_POOL: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

VIEWPORTS: list[dict] = [
    {"width": 1366, "height": 768},
    {"width": 1366, "height": 900},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1920, "height": 1080},
]

LOCALES = ["en-US", "en-GB", "en-CA"]
TIMEZONES = ["America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London"]


def random_fingerprint(seed: int | None = None) -> Fingerprint:
    """Return a deterministic fingerprint when seed is provided."""

    rng = random.Random(seed)
    return Fingerprint(
        user_agent=rng.choice(UA_POOL),
        viewport=dict(rng.choice(VIEWPORTS)),
        locale=rng.choice(LOCALES),
        timezone_id=rng.choice(TIMEZONES),
    )


STEALTH_FINGERPRINT = random_fingerprint(seed=0)
