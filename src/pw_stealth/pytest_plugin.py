"""Pytest fixtures for applying stealth to a user's own Playwright tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from .stealth import BrowserFingerprint
from .sync_stealth import apply_stealth_sync


@pytest.fixture
def stealth_fingerprint() -> BrowserFingerprint | None:
    """Override in a test suite to provide a FingerprintProfile or Fingerprint."""

    return None


@pytest.fixture
def stealth_context(browser, stealth_fingerprint: BrowserFingerprint | None) -> Iterator:
    """Return a Playwright context with pw_stealth init scripts installed."""

    context = browser.new_context()
    apply_stealth_sync(context, fingerprint=stealth_fingerprint)
    try:
        yield context
    finally:
        context.close()


@pytest.fixture
def stealth_page(stealth_context) -> Iterator:
    """Return a new page from the stealth-enabled Playwright context."""

    page = stealth_context.new_page()
    try:
        yield page
    finally:
        page.close()
