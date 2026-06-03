"""Command-line diagnostics for authorized Playwright stealth checks."""

from __future__ import annotations

import argparse
import json
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .sync_stealth import stealth_context_sync

CHECK_SCRIPT = """
() => {
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

  return {
    url: location.href,
    title: document.title,
    webdriverType: typeof navigator.webdriver,
    webdriverValue: String(navigator.webdriver),
    pluginsLength: navigator.plugins ? navigator.plugins.length : null,
    language: navigator.language || null,
    languages: navigator.languages ? Array.from(navigator.languages) : [],
    userAgent: navigator.userAgent,
    hardwareConcurrency: navigator.hardwareConcurrency || null,
    deviceMemory: navigator.deviceMemory || null,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    webglVendor: webgl.vendor,
    webglRenderer: webgl.renderer
  };
}
"""


def collect_detection_signals(page) -> dict[str, Any]:
    """Collect browser-exposed detection signals from the current page."""

    return page.evaluate(CHECK_SCRIPT)


def format_detection_signals(signals: dict[str, Any]) -> str:
    """Format signal output for humans."""

    rows = [
        ("url", signals.get("url")),
        ("title", signals.get("title")),
        ("navigator.webdriver type", signals.get("webdriverType")),
        ("navigator.webdriver value", signals.get("webdriverValue")),
        ("navigator.plugins.length", signals.get("pluginsLength")),
        ("navigator.language", signals.get("language")),
        ("navigator.languages", signals.get("languages")),
        ("navigator.hardwareConcurrency", signals.get("hardwareConcurrency")),
        ("navigator.deviceMemory", signals.get("deviceMemory")),
        ("Intl timezone", signals.get("timezone")),
        ("WebGL vendor", signals.get("webglVendor")),
        ("WebGL renderer", signals.get("webglRenderer")),
        ("navigator.userAgent", signals.get("userAgent")),
    ]
    return "\n".join(f"{name}: {value}" for name, value in rows)


def check_url(args: argparse.Namespace) -> int:
    with sync_playwright() as playwright:
        context = stealth_context_sync(playwright, headless=args.headless)
        page = context.new_page()
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout)
            signals = collect_detection_signals(page)
        except PlaywrightTimeoutError as exc:
            print(f"Timed out loading {args.url}: {exc}")
            return 2
        finally:
            context.close()

    if args.json:
        print(json.dumps(signals, indent=2, sort_keys=True))
    else:
        print(format_detection_signals(signals))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pw-stealth",
        description="Diagnostics for authorized Playwright stealth testing.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Open a URL with stealth and print signals.")
    check.add_argument("url", help="Authorized test URL to open.")
    check.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run Chromium headless. Defaults to true.",
    )
    check.add_argument(
        "--timeout",
        type=int,
        default=30_000,
        help="Navigation timeout in milliseconds.",
    )
    check.add_argument("--json", action="store_true", help="Print raw JSON signals.")
    check.set_defaults(func=check_url)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
