"""Command-line diagnostics for authorized Playwright stealth checks."""

from __future__ import annotations

import argparse
import json
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .presets import load_preset, preset_engine, preset_names
from .sync_stealth import stealth_context_sync

CREEPJS_URL = "https://abrahamjuliot.github.io/creepjs/"

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

# Reads the trust score and lie signals that the CreepJS detection page renders into the
# DOM. CreepJS exposes these as text nodes (the "trust score" percentage and a "lies"
# count), so we scrape the rendered values rather than hooking its internals.
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


def collect_detection_signals(page) -> dict[str, Any]:
    """Collect browser-exposed detection signals from the current page."""

    return page.evaluate(CHECK_SCRIPT)


def collect_creepjs_signals(page) -> dict[str, Any]:
    """Scrape the trust score and lie signals rendered by a CreepJS-style page."""

    return page.evaluate(CREEPJS_SCRAPE_SCRIPT)


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


def format_creepjs_signals(signals: dict[str, Any]) -> str:
    """Format parsed CreepJS trust/lie signals for humans."""

    rows = [
        ("url", signals.get("url")),
        ("title", signals.get("title")),
        ("trust score", signals.get("trust")),
        ("lies", signals.get("lies")),
        ("fingerprint id", signals.get("fingerprintId")),
        ("bot signal", signals.get("bot")),
    ]
    return "\n".join(f"{name}: {value}" for name, value in rows)


def _resolve_target(args: argparse.Namespace) -> str:
    if getattr(args, "creepjs", False):
        return CREEPJS_URL
    return args.url


def check_url(args: argparse.Namespace) -> int:
    target = _resolve_target(args)
    if target is None:
        print("Provide a URL or pass --creepjs.")
        return 2

    fingerprint = load_preset(args.preset) if args.preset else None
    wait_until = "networkidle" if args.creepjs else "domcontentloaded"

    with sync_playwright() as playwright:
        context = stealth_context_sync(
            playwright,
            headless=args.headless,
            fingerprint=fingerprint,
        )
        page = context.new_page()
        try:
            page.goto(target, wait_until=wait_until, timeout=args.timeout)
            if args.creepjs:
                signals = collect_creepjs_signals(page)
            else:
                signals = collect_detection_signals(page)
        except PlaywrightTimeoutError as exc:
            print(f"Timed out loading {target}: {exc}")
            return 2
        finally:
            context.close()

    if args.json:
        print(json.dumps(signals, indent=2, sort_keys=True))
    elif args.creepjs:
        print(format_creepjs_signals(signals))
    else:
        print(format_detection_signals(signals))
    return 0


def list_profiles(args: argparse.Namespace) -> int:
    names = preset_names()
    if args.json:
        payload = {name: {"engine": preset_engine(name)} for name in names}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Available fingerprint presets:")
        for name in names:
            print(f"  {name} ({preset_engine(name)})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pw-stealth",
        description="Diagnostics for authorized Playwright stealth testing.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Open a URL with stealth and print signals.")
    check.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Authorized test URL to open. Optional when --creepjs is set.",
    )
    check.add_argument(
        "--creepjs",
        action="store_true",
        help="Open a CreepJS-style detection page and report parsed trust/lie signals.",
    )
    check.add_argument(
        "--preset",
        choices=preset_names(),
        default=None,
        help="Apply a named fingerprint preset before checking.",
    )
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

    profiles = subparsers.add_parser("profiles", help="List available fingerprint presets.")
    profiles.add_argument("--json", action="store_true", help="Print presets as JSON.")
    profiles.set_defaults(func=list_profiles)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
