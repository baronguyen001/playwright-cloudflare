# playwright-cloudflare

Playwright stealth defaults for common Cloudflare checks: anti-detect launch args,
`add_init_script` patches, persistent Chrome profiles, and small fingerprint randomization.

![Sannysoft webdriver check](screenshots/sannysoft_webdriver.svg)

**Disclaimer:** For authorized testing and your own properties only. Respect robots.txt and
Terms of Service. Do not use this to access sites that prohibit automated access. No CAPTCHA
solving, proxy rotation, or platform-specific bypass is included. See [DISCLAIMER.md](DISCLAIMER.md).

## Install

```bash
pip install playwright-cloudflare
playwright install chromium
```

## 30-second usage

```python
from playwright.sync_api import sync_playwright
from pw_stealth import stealth_context

with sync_playwright() as p:
    ctx = stealth_context(p, headless=False)
    page = ctx.new_page()
    page.goto("https://bot.sannysoft.com")
    page.screenshot(path="sannysoft.png", full_page=True)
    ctx.close()
```

## Included

- `STEALTH_ARGS` without `--enable-automation`
- `STEALTH_INIT_JS` for `navigator.webdriver`, `window.chrome`, plugins, and languages
- Random desktop `Fingerprint` values for user agent, viewport, locale, and timezone
- Persistent Chrome profile support with `--profile-directory=...`

## Not included

No CAPTCHA solver, no proxy rotation, and no per-platform bypass logic. For persistent session
testing, use `channel="chrome"`, a real Chrome profile path, and `headless=True` to add
`--headless=new`.

Read the [disclaimer](DISCLAIMER.md) before using.

Built by [barobaonguyen](https://github.com/barobaonguyen). Want the full **scrape -> AI -> alert** bot, not just this piece? -> **[Trawlkit](https://github.com/barobaonguyen)** (one-time kit).
