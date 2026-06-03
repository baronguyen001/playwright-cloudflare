"""Explicit Playwright sync-API stealth helpers."""

from __future__ import annotations

from .stealth import BrowserFingerprint
from .stealth import apply_stealth as _apply_stealth
from .stealth import stealth_browser as _stealth_browser
from .stealth import stealth_context as _stealth_context


def stealth_browser_sync(
    playwright,
    *,
    headless: bool = False,
    proxy: str | None = None,
    channel: str | None = None,
    extra_args: list[str] | None = None,
):
    """Launch Chromium for Playwright's sync API with stealth launch arguments."""

    return _stealth_browser(
        playwright,
        headless=headless,
        proxy=proxy,
        channel=channel,
        extra_args=extra_args,
    )


def stealth_context_sync(
    playwright,
    *,
    user_data_dir: str | None = None,
    headless: bool = False,
    proxy: str | None = None,
    fingerprint: BrowserFingerprint | None = None,
    channel: str | None = None,
):
    """Return a sync BrowserContext with fingerprint options and init scripts applied."""

    return _stealth_context(
        playwright,
        user_data_dir=user_data_dir,
        headless=headless,
        proxy=proxy,
        fingerprint=fingerprint,
        channel=channel,
    )


def apply_stealth_sync(
    context_or_page,
    *,
    fingerprint: BrowserFingerprint | None = None,
) -> None:
    """Install stealth init scripts on a sync BrowserContext or Page."""

    _apply_stealth(context_or_page, fingerprint=fingerprint)
