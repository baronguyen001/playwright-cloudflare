"""Opt-in fingerprint profile diagnostics against Sannysoft."""

from playwright.sync_api import sync_playwright

from pw_stealth import FingerprintProfile, stealth_context_sync

profile = FingerprintProfile(
    locale="en-US",
    timezone_id="America/New_York",
    hardware_concurrency=8,
    device_memory=8,
    webgl_vendor="Google Inc.",
    webgl_renderer="ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)",
    canvas_noise=True,
)

with sync_playwright() as p:
    context = stealth_context_sync(p, headless=False, fingerprint=profile)
    page = context.new_page()
    page.goto("https://bot.sannysoft.com", wait_until="networkidle")
    page.screenshot(path="fingerprint_profile.png", full_page=True)
    context.close()
