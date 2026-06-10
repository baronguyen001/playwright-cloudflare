"""Named, internally-consistent FingerprintProfile presets for authorized testing.

Each preset bundles the existing fingerprint vectors (user agent, locale/languages,
timezone, hardware concurrency, device memory, WebGL vendor/renderer) into a coherent
desktop identity so the values do not contradict one another. For example, a Chrome
preset reports a Chrome user agent together with a Google/ANGLE WebGL renderer, while a
Firefox preset pairs a Gecko user agent with a Mozilla WebGL vendor.

Presets are opt-in. They produce a :class:`~pw_stealth.fingerprint.FingerprintProfile`
that you pass to ``stealth_context``/``stealth_context_sync`` exactly like a hand-built
profile. Nothing here solves CAPTCHAs, rotates proxies, or bypasses any specific service.
"""

from __future__ import annotations

from .fingerprint import FingerprintProfile

# Engine families that must agree with the rest of a preset's vectors. Chromium-based
# browsers (Chrome, Edge, Brave) expose a Google/ANGLE WebGL identity and a "chrome"
# navigator surface; Gecko (Firefox) exposes a Mozilla WebGL identity and no window.chrome.
CHROMIUM = "chromium"
GECKO = "gecko"

_CHROMIUM_VENDORS = {"Google Inc.", "Google Inc. (Intel)", "Google Inc. (NVIDIA)"}
_GECKO_VENDORS = {"Mozilla"}


def _chrome_profile() -> FingerprintProfile:
    return FingerprintProfile(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        languages=("en-US", "en"),
        timezone_id="America/New_York",
        hardware_concurrency=8,
        device_memory=8,
        webgl_vendor="Google Inc. (Intel)",
        webgl_renderer=(
            "ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        ),
        canvas_noise=True,
        canvas_noise_seed=125,
    )


def _edge_profile() -> FingerprintProfile:
    return FingerprintProfile(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
        ),
        viewport={"width": 1536, "height": 864},
        locale="en-US",
        languages=("en-US", "en"),
        timezone_id="America/Chicago",
        hardware_concurrency=12,
        device_memory=16,
        webgl_vendor="Google Inc. (NVIDIA)",
        webgl_renderer=(
            "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        ),
        canvas_noise=True,
        canvas_noise_seed=64,
    )


def _brave_profile() -> FingerprintProfile:
    # Brave ships a Chrome user agent (it masks as Chrome on purpose) and a Chromium
    # WebGL surface, so it stays in the Chromium family for consistency checks.
    return FingerprintProfile(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1440, "height": 900},
        locale="en-US",
        languages=("en-US", "en"),
        timezone_id="America/Los_Angeles",
        hardware_concurrency=8,
        device_memory=8,
        webgl_vendor="Google Inc.",
        webgl_renderer="ANGLE (Apple, Apple M2, OpenGL 4.1 Metal - 88)",
        canvas_noise=True,
        canvas_noise_seed=42,
    )


def _firefox_profile() -> FingerprintProfile:
    # Gecko: Mozilla WebGL vendor, no Chromium ANGLE prefix, no window.chrome surface.
    return FingerprintProfile(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) "
            "Gecko/20100101 Firefox/126.0"
        ),
        viewport={"width": 1366, "height": 768},
        locale="en-GB",
        languages=("en-GB", "en"),
        timezone_id="Europe/London",
        hardware_concurrency=8,
        device_memory=8,
        webgl_vendor="Mozilla",
        webgl_renderer="Mozilla",
        canvas_noise=True,
        canvas_noise_seed=126,
    )


_PRESETS: dict[str, tuple[str, FingerprintProfile]] = {
    "chrome": (CHROMIUM, _chrome_profile()),
    "edge": (CHROMIUM, _edge_profile()),
    "brave": (CHROMIUM, _brave_profile()),
    "firefox": (GECKO, _firefox_profile()),
}


def preset_names() -> list[str]:
    """Return the sorted list of available preset names."""

    return sorted(_PRESETS)


def preset_engine(name: str) -> str:
    """Return the engine family (``chromium`` or ``gecko``) backing a preset."""

    try:
        return _PRESETS[name.lower()][0]
    except KeyError:
        raise _unknown_preset(name) from None


def load_preset(name: str) -> FingerprintProfile:
    """Return the :class:`FingerprintProfile` for a named preset.

    Names are case-insensitive. Raises ``ValueError`` for unknown presets.
    """

    try:
        return _PRESETS[name.lower()][1]
    except KeyError:
        raise _unknown_preset(name) from None


def _unknown_preset(name: str) -> ValueError:
    available = ", ".join(preset_names())
    return ValueError(f"unknown preset {name!r}; available presets: {available}")


def is_internally_consistent(name: str) -> bool:
    """Return True when a preset's vectors agree across user agent, WebGL, and engine.

    This is the same coherence contract the presets are built to satisfy: the WebGL
    vendor must match the engine family, the user-agent token must match the engine,
    and any locale/language pair must share the same base language.
    """

    engine, profile = _PRESETS[name.lower()]
    ua = profile.user_agent or ""

    if engine == CHROMIUM:
        if profile.webgl_vendor not in _CHROMIUM_VENDORS:
            return False
        # Chromium UAs always carry the "Chrome/" token (Edge/Brave included).
        if "Chrome/" not in ua:
            return False
        if "Firefox/" in ua or "Gecko/20100101" in ua:
            return False
    elif engine == GECKO:
        if profile.webgl_vendor not in _GECKO_VENDORS:
            return False
        if "Firefox/" not in ua or "Gecko/" not in ua:
            return False
        if "Chrome/" in ua:
            return False
    else:  # pragma: no cover - guarded by preset construction
        return False

    # Locale and the resolved language list must agree on the base language.
    languages = profile.resolved_languages
    if profile.locale is not None and languages:
        base = profile.locale.split("-", maxsplit=1)[0]
        if not any(lang.split("-", maxsplit=1)[0] == base for lang in languages):
            return False

    return True
