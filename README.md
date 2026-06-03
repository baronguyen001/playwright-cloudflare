# playwright-cloudflare

Playwright stealth defaults for authorized browser testing: launch args,
`add_init_script` patches, persistent Chrome profiles, explicit sync helpers, and
opt-in fingerprint profile controls.

![Sannysoft webdriver check](screenshots/sannysoft_webdriver.svg)

**Disclaimer:** For authorized testing and your own properties only. Respect robots.txt and
Terms of Service. Do not use this to access sites that prohibit automated access. No CAPTCHA
solving, proxy rotation, credential stuffing, or platform-specific bypass is included. See
[DISCLAIMER.md](DISCLAIMER.md) before use.

## Install

```bash
pip install playwright-cloudflare
playwright install chromium
```

The package keeps the no-extra-stealth-dependency design: Playwright is the only runtime
dependency.

## Sync Usage

Use the explicit sync helpers with Playwright's sync API:

```python
from playwright.sync_api import sync_playwright
from pw_stealth import stealth_context_sync

with sync_playwright() as p:
    ctx = stealth_context_sync(p, headless=False)
    page = ctx.new_page()
    page.goto("https://bot.sannysoft.com", wait_until="networkidle")
    page.screenshot(path="sannysoft.png", full_page=True)
    ctx.close()
```

For an existing sync `Page` or `BrowserContext`, install the init script directly:

```python
from pw_stealth import apply_stealth_sync

apply_stealth_sync(page)
```

The legacy `stealth_context`, `stealth_browser`, and `apply_stealth` imports remain
available for existing users.

## Fingerprint Profiles

`FingerprintProfile` is opt-in: only fields you set are applied. Locale and timezone values
are passed to Playwright context options and mirrored in init-script patches where browser
diagnostics commonly read them.

```python
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

context = stealth_context_sync(p, fingerprint=profile, headless=True)
```

| Vector | Field | Applied through |
| --- | --- | --- |
| User agent | `user_agent` | Playwright context option |
| Viewport | `viewport` | Playwright context option |
| Locale and languages | `locale`, `languages` | Context option plus `navigator.language(s)` |
| Timezone | `timezone_id` | Context option plus `Intl.DateTimeFormat` |
| CPU threads | `hardware_concurrency` | `navigator.hardwareConcurrency` |
| Device memory | `device_memory` | `navigator.deviceMemory` |
| WebGL identity | `webgl_vendor`, `webgl_renderer` | WebGL `getParameter` patch |
| Canvas readout noise | `canvas_noise` | Canvas read APIs |

## CLI

`pw-stealth check <url>` opens an authorized test page with stealth on and prints detection
signals such as `navigator.webdriver`, plugin count, languages, timezone, and WebGL values.

```bash
pw-stealth check https://example.com
pw-stealth check https://bot.sannysoft.com --no-headless --json
```

## Included

- `STEALTH_ARGS` without `--enable-automation`
- `STEALTH_INIT_JS` for `navigator.webdriver`, `window.chrome`, plugins, and languages
- Random desktop `Fingerprint` values for user agent, viewport, locale, and timezone
- Explicit sync helpers in `pw_stealth.sync_stealth`
- Opt-in `FingerprintProfile` vectors for WebGL, canvas, locale, timezone, CPU, and memory
- Persistent Chrome profile support with `--profile-directory=...`

## Not Included

No CAPTCHA solver, no proxy rotation, no credential workflows, and no per-platform bypass
logic. For persistent session testing, use `channel="chrome"`, a real Chrome profile path,
and `headless=True` to add `--headless=new`.

Built by [barobaonguyen](https://github.com/barobaonguyen). Want the full **scrape -> AI -> alert** bot, not just this piece? → **[Trawlkit](https://github.com/barobaonguyen)** (one-time kit).
