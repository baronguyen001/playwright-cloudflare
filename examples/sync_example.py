"""Minimal Playwright sync-API usage against example.com."""

from playwright.sync_api import sync_playwright

from pw_stealth import stealth_context_sync

with sync_playwright() as p:
    context = stealth_context_sync(p, headless=True)
    page = context.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    print(page.title())
    context.close()
