"""Playwright launch helpers with init-script stealth patches."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .fingerprint import Fingerprint, random_fingerprint

if TYPE_CHECKING:
    pass


STEALTH_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
]

STEALTH_INIT_JS: str = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
  parameters.name === 'notifications'
    ? Promise.resolve({ state: Notification.permission })
    : originalQuery(parameters)
);
"""


def _merge_args(extra_args: list[str] | None = None, *, headless: bool = False) -> list[str]:
    merged = list(STEALTH_ARGS)
    if headless:
        merged.append("--headless=new")
    for arg in extra_args or []:
        if arg == "--enable-automation":
            continue
        if arg not in merged:
            merged.append(arg)
    return merged


def _proxy(proxy: str | None):
    return {"server": proxy} if proxy else None


def _resolve_chrome_profile(user_data_dir: str) -> tuple[str, list[str], str | None]:
    path = Path(user_data_dir)
    launch_dir = str(path)
    launch_args: list[str] = []
    channel: str | None = None

    profile_name = path.name
    parent_name = path.parent.name.lower() if path.parent else ""
    is_profile_path = parent_name == "user data" and (
        profile_name.lower().startswith("profile ") or profile_name.lower() == "default"
    )
    if is_profile_path:
        launch_dir = str(path.parent)
        launch_args.append(f"--profile-directory={profile_name}")

    lowered = launch_dir.lower().replace("/", "\\")
    if "\\google\\chrome\\user data" in lowered:
        channel = "chrome"

    return launch_dir, launch_args, channel


def _context_options(fingerprint: Fingerprint | None, proxy: str | None) -> dict:
    fp = fingerprint or random_fingerprint()
    return {
        "user_agent": fp.user_agent,
        "viewport": dict(fp.viewport),
        "locale": fp.locale,
        "timezone_id": fp.timezone_id,
        "proxy": _proxy(proxy),
    }


def stealth_browser(
    playwright,
    *,
    headless: bool = False,
    proxy: str | None = None,
    channel: str | None = None,
    extra_args: list[str] | None = None,
):
    """Launch a non-persistent Chromium with STEALTH_ARGS merged in. Returns a Browser."""

    return playwright.chromium.launch(
        headless=headless,
        proxy=_proxy(proxy),
        channel=channel,
        args=_merge_args(extra_args, headless=headless),
    )


def stealth_context(
    playwright,
    *,
    user_data_dir: str | None = None,
    headless: bool = False,
    proxy: str | None = None,
    fingerprint: Fingerprint | None = None,
    channel: str | None = None,
):
    """Return a BrowserContext with fingerprint options and stealth init script applied."""

    options = _context_options(fingerprint, proxy)
    if user_data_dir:
        launch_dir, profile_args, profile_channel = _resolve_chrome_profile(user_data_dir)
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=launch_dir,
            headless=headless,
            channel=channel or profile_channel,
            args=_merge_args(profile_args, headless=headless),
            **options,
        )
    else:
        browser = stealth_browser(playwright, headless=headless, proxy=proxy, channel=channel)
        context = browser.new_context(
            user_agent=options["user_agent"],
            viewport=options["viewport"],
            locale=options["locale"],
            timezone_id=options["timezone_id"],
        )
    apply_stealth(context)
    return context


def apply_stealth(context_or_page) -> None:
    """Install STEALTH_INIT_JS on a BrowserContext or Page before site scripts run."""

    context_or_page.add_init_script(STEALTH_INIT_JS)
