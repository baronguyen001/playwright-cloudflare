"""Machine-readable stealth audit reports for authorized test pages."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .presets import load_preset
from .sync_stealth import stealth_context_sync

AUDIT_SCHEMA_VERSION = 1
CREEPJS_URL = "https://abrahamjuliot.github.io/creepjs/"

AUDIT_SCRIPT = r"""
() => {
  const stableHash = (value) => {
    let hash = 0;
    const text = String(value || "");
    for (let i = 0; i < text.length; i += 1) {
      hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0;
    }
    return String(hash >>> 0);
  };

  const webgl = (() => {
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      if (!gl) return { vendor: null, renderer: null };
      const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
      if (!debugInfo) return { vendor: null, renderer: null };
      return {
        vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
        renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
      };
    } catch (_) {
      return { vendor: null, renderer: null };
    }
  })();

  const canvas = (() => {
    try {
      const canvas = document.createElement("canvas");
      canvas.width = 220;
      canvas.height = 30;
      const context = canvas.getContext("2d");
      if (!context) return { available: false, dataUrlHash: null, dataUrlLength: null };
      context.textBaseline = "top";
      context.font = "16px Arial";
      context.fillStyle = "#f60";
      context.fillRect(0, 0, 220, 30);
      context.fillStyle = "#069";
      context.fillText("pw-stealth audit", 4, 6);
      const dataUrl = canvas.toDataURL();
      return {
        available: true,
        dataUrlHash: stableHash(dataUrl),
        dataUrlLength: dataUrl.length
      };
    } catch (_) {
      return { available: false, dataUrlHash: null, dataUrlLength: null };
    }
  })();

  return {
    page: {
      url: location.href,
      title: document.title
    },
    navigator: {
      webdriverPresent: "webdriver" in navigator,
      webdriverType: typeof navigator.webdriver,
      webdriverValue: navigator.webdriver === undefined ? null : navigator.webdriver,
      webdriverString: String(navigator.webdriver),
      pluginsLength: navigator.plugins ? navigator.plugins.length : null,
      mimeTypesLength: navigator.mimeTypes ? navigator.mimeTypes.length : null,
      language: navigator.language || null,
      languages: navigator.languages ? Array.from(navigator.languages) : [],
      userAgent: navigator.userAgent,
      platform: navigator.platform || null,
      hardwareConcurrency: navigator.hardwareConcurrency || null,
      deviceMemory: navigator.deviceMemory || null
    },
    timezone: {
      name: Intl.DateTimeFormat().resolvedOptions().timeZone,
      offsetMinutes: new Date().getTimezoneOffset()
    },
    webgl,
    canvas
  };
}
"""

# Reads the trust score and lie signals rendered by a CreepJS-style page. The parser keeps
# the package independent from CreepJS internals and is intended only for defensive testing.
CREEPJS_SCRAPE_SCRIPT = r"""
() => {
  const text = (document.body && document.body.innerText) || "";
  const pick = (regex) => {
    const match = text.match(regex);
    return match ? match[1].trim() : null;
  };
  return {
    url: location.href,
    title: document.title,
    trust: pick(/trust score[^0-9]*([0-9.]+\s*%[^\n]*)/i),
    lies: pick(/(\d+)\s+lies?\b/i),
    fingerprintId: pick(/\bvisitor[^0-9a-z]*([0-9a-z]{6,})/i),
    bot: pick(/\bbot\b[^\n:]*:?\s*([^\n]+)/i),
    rawLength: text.length
  };
}
"""


class AuditComparisonError(Exception):
    """Raised by callers that want to treat audit diffs as regressions."""


def collect_audit_signals(page) -> dict[str, Any]:
    """Collect browser-exposed signals from the current page."""

    return page.evaluate(AUDIT_SCRIPT)


def collect_creepjs_signals(page) -> dict[str, Any]:
    """Scrape trust and lie signals rendered by a CreepJS-style page."""

    return page.evaluate(CREEPJS_SCRAPE_SCRIPT)


def build_audit_report(
    *,
    requested_url: str,
    signals: dict[str, Any],
    creepjs: dict[str, Any] | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Return the stable JSON payload used for CI regression checks."""

    report: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "tool": "pw_stealth.audit",
        "requested_url": requested_url,
        "preset": preset,
        "signals": signals,
    }
    if creepjs is not None:
        report["creepjs"] = creepjs
    return report


def run_audit_sync(
    url: str,
    *,
    preset: str | None = None,
    creepjs: bool = False,
    headless: bool = True,
    timeout: int = 30_000,
) -> dict[str, Any]:
    """Open a URL with stealth enabled and return a machine-readable report."""

    fingerprint = load_preset(preset) if preset else None
    wait_until = "networkidle" if creepjs else "domcontentloaded"

    with sync_playwright() as playwright:
        context = stealth_context_sync(
            playwright,
            headless=headless,
            fingerprint=fingerprint,
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until=wait_until, timeout=timeout)
            signals = collect_audit_signals(page)
            creepjs_signals = collect_creepjs_signals(page) if creepjs else None
        finally:
            context.close()

    return build_audit_report(
        requested_url=url,
        signals=signals,
        creepjs=creepjs_signals,
        preset=preset,
    )


def read_report(path: str | Path) -> dict[str, Any]:
    """Read an audit report JSON file."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_report(report: dict[str, Any], path: str | Path) -> None:
    """Write an audit report JSON file with stable formatting."""

    Path(path).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def compare_reports(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return leaf-level diffs between comparable audit report sections."""

    diffs: list[dict[str, Any]] = []
    for root in ("signals", "creepjs"):
        current_value = current.get(root)
        baseline_value = baseline.get(root)
        if current_value is None and baseline_value is None:
            continue
        diffs.extend(_compare_values((root,), current_value, baseline_value))
    return diffs


def format_diffs(diffs: Iterable[dict[str, Any]]) -> str:
    """Format audit diffs for CLI output."""

    rows = []
    for diff in diffs:
        rows.append(
            f"{diff['path']}: baseline={diff['baseline']!r} current={diff['current']!r}"
        )
    return "\n".join(rows)


def _compare_values(
    path: tuple[str, ...],
    current: Any,
    baseline: Any,
) -> list[dict[str, Any]]:
    if isinstance(current, dict) and isinstance(baseline, dict):
        diffs: list[dict[str, Any]] = []
        for key in sorted(set(current) | set(baseline)):
            diffs.extend(_compare_values((*path, str(key)), current.get(key), baseline.get(key)))
        return diffs

    if current != baseline:
        return [
            {
                "path": ".".join(path),
                "baseline": baseline,
                "current": current,
            }
        ]
    return []


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "AUDIT_SCRIPT",
    "CREEPJS_SCRAPE_SCRIPT",
    "CREEPJS_URL",
    "AuditComparisonError",
    "PlaywrightTimeoutError",
    "build_audit_report",
    "collect_audit_signals",
    "collect_creepjs_signals",
    "compare_reports",
    "format_diffs",
    "read_report",
    "run_audit_sync",
    "write_report",
]
