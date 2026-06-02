"""Open bot.sannysoft.com and save a webdriver-focused screenshot."""

from playwright.sync_api import sync_playwright

from pw_stealth import stealth_context

with sync_playwright() as p:
    context = stealth_context(p, headless=False)
    page = context.new_page()
    page.goto("https://bot.sannysoft.com", wait_until="networkidle")
    page.screenshot(path="sannysoft.png", full_page=True)
    context.close()
