"""Apply a named fingerprint preset, then check signals against a CreepJS-style page.

For authorized testing and your own properties only. See DISCLAIMER.md.
"""

from playwright.sync_api import sync_playwright

from pw_stealth import is_internally_consistent, load_preset, preset_names, stealth_context_sync

CREEPJS_URL = "https://abrahamjuliot.github.io/creepjs/"

# Pick any of: chrome, edge, brave, firefox.
print("Available presets:", ", ".join(preset_names()))

profile = load_preset("chrome")
assert is_internally_consistent("chrome")  # vectors agree (UA <-> WebGL <-> engine)

with sync_playwright() as p:
    context = stealth_context_sync(p, headless=True, fingerprint=profile)
    page = context.new_page()
    page.goto(CREEPJS_URL, wait_until="networkidle")
    page.screenshot(path="creepjs_chrome_preset.png", full_page=True)
    print("Saved creepjs_chrome_preset.png")
    context.close()
