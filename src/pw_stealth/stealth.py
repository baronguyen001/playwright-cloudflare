"""Playwright launch helpers with init-script stealth patches."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

from .fingerprint import (
    Fingerprint,
    FingerprintProfile,
    fingerprint_context_options,
    fingerprint_init_script,
    random_fingerprint,
)

STEALTH_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
]

STEALTH_INIT_JS: str = """
(() => {
  const defineNavigatorGetter = (name, value) => {
    const readValue = () => Array.isArray(value) ? value.slice() : value;
    const descriptor = { get: readValue, configurable: true };
    try {
      Object.defineProperty(Navigator.prototype, name, descriptor);
    } catch (_) {
      try {
        Object.defineProperty(navigator, name, descriptor);
      } catch (_) {}
    }
  };

  defineNavigatorGetter("webdriver", undefined);
  defineNavigatorGetter("plugins", [1, 2, 3, 4, 5]);
  defineNavigatorGetter("language", "en-US");
  defineNavigatorGetter("languages", ["en-US", "en"]);
  window.chrome = window.chrome || {};
  window.chrome.runtime = window.chrome.runtime || {};

  if (window.navigator.permissions && window.navigator.permissions.query) {
    const originalQuery = window.navigator.permissions.query.bind(
      window.navigator.permissions
    );
    window.navigator.permissions.query = (parameters) => (
      parameters && parameters.name === "notifications"
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
    );
  }
})();
"""

BrowserFingerprint = Fingerprint | FingerprintProfile


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
    path = (
        PureWindowsPath(user_data_dir)
        if "\\" in user_data_dir or ":" in user_data_dir[:3]
        else Path(user_data_dir)
    )
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


def _resolve_fingerprint(fingerprint: BrowserFingerprint | None) -> BrowserFingerprint:
    return fingerprint or random_fingerprint()


def _context_options(fingerprint: BrowserFingerprint | None, proxy: str | None = None) -> dict:
    options = fingerprint_context_options(fingerprint)
    if proxy:
        options["proxy"] = _proxy(proxy)
    return options


def _stealth_init_script(fingerprint: BrowserFingerprint | None = None) -> str:
    profile_script = fingerprint_init_script(fingerprint)
    if not profile_script:
        return STEALTH_INIT_JS
    return f"{STEALTH_INIT_JS}\n{profile_script}"


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
    fingerprint: BrowserFingerprint | None = None,
    channel: str | None = None,
):
    """Return a BrowserContext with fingerprint options and stealth init script applied."""

    resolved_fingerprint = _resolve_fingerprint(fingerprint)
    options = _context_options(resolved_fingerprint, proxy if user_data_dir else None)
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
        context = browser.new_context(**options)
    apply_stealth(context, fingerprint=resolved_fingerprint)
    return context


def apply_stealth(
    context_or_page,
    *,
    fingerprint: BrowserFingerprint | None = None,
) -> None:
    """Install STEALTH_INIT_JS on a BrowserContext or Page before site scripts run."""

    context_or_page.add_init_script(_stealth_init_script(fingerprint))
