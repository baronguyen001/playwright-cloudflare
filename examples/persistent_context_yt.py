"""Persistent Chrome profile pattern for authorized session testing."""

from playwright.sync_api import sync_playwright

from pw_stealth import Fingerprint, stealth_context

REAL_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

with sync_playwright() as p:
    context = stealth_context(
        p,
        user_data_dir="/path/to/your/chrome/User Data",
        headless=True,
        channel="chrome",
        fingerprint=Fingerprint(
            user_agent=REAL_CHROME_UA,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
        ),
    )
    page = context.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    assert page.title()
    context.close()
