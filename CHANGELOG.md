# Changelog

## 0.4.0 - 2026-06-11

- Added `pw_stealth.audit` for machine-readable JSON reports that capture
  `navigator`, plugin, WebGL, canvas, timezone, and optional CreepJS-style trust/lie
  signals from authorized diagnostic pages.
- Added `pw-stealth audit <url> --json out.json` plus `--compare baseline.json`; compare
  mode prints signal diffs and exits non-zero when the current stealth setup differs from
  a saved CI baseline.
- Added `pw_stealth.pytest_plugin` with `stealth_context` and `stealth_page` fixtures,
  exposed via a `pytest11` entry point and optional `[test]` extra.
- Added mocked audit and fixture smoke tests plus `examples/audit_ci.py`.
- Kept the no-extra-stealth-dependency design and the defensive/testing-only disclaimer.

## 0.3.0 - 2026-06-10

- Added `pw_stealth.presets` with internally-consistent `chrome`, `edge`, `brave`, and `firefox` fingerprint presets; exposed `load_preset`, `preset_names`, `preset_engine`, and `is_internally_consistent`.
- Extended the CLI: `pw-stealth profiles` lists presets, `pw-stealth check --preset <name>` applies one before checking, and `pw-stealth check --creepjs` opens a CreepJS-style detection page and reports parsed trust/lie signals.
- Added `tests/test_presets.py` (per-preset internal-consistency) and a fully mocked `tests/test_cli.py` smoke suite that launches no live browser.
- Added `examples/preset_example.py` using `example.com`/CreepJS only.
- Kept the no-extra-stealth-dependency design (Playwright remains the only runtime dependency).

## 0.2.0 - 2026-06-03

- Added explicit Playwright sync-API helpers in `pw_stealth.sync_stealth`, including `apply_stealth_sync`.
- Added opt-in `FingerprintProfile` vectors for WebGL vendor/renderer, canvas readout noise, locale, timezone, hardware concurrency, and device memory.
- Added the `pw-stealth check <url>` CLI for authorized detection-signal diagnostics.
- Added sync and fingerprint-profile examples using `example.com` and Sannysoft.
- Updated README usage, fingerprint vector documentation, and defensive-use framing.

## 0.1.0 - 2026-06-02

- Initial release with stealth launch args, init script patches, fingerprint randomization, and persistent-context helpers.
