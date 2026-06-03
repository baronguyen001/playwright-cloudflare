"""Persistent Chrome profile pattern for authorized session testing."""

from playwright.sync_api import sync_playwright

from pw_stealth import FingerprintProfile, stealth_context_sync

REAL_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

with sync_playwright() as p:
    context = stealth_context_sync(
        p,
        user_data_dir="/path/to/your/chrome/User Data",
        headless=True,
        channel="chrome",
        fingerprint=FingerprintProfile(
            user_agent=REAL_CHROME_UA,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
            hardware_concurrency=8,
            device_memory=8,
        ),
    )
    page = context.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    assert page.title()
    context.close()
