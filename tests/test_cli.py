"""CLI smoke tests. Playwright is mocked: no live browser is launched in CI."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pw_stealth import cli


class FakePage:
    """Records init scripts and returns a canned evaluate() result."""

    def __init__(self, evaluate_result: dict[str, Any]) -> None:
        self._evaluate_result = evaluate_result
        self.goto_calls: list[tuple[str, dict[str, Any]]] = []
        self.evaluate_calls: list[str] = []

    def goto(self, url: str, **kwargs: Any) -> None:
        self.goto_calls.append((url, kwargs))

    def evaluate(self, script: str) -> dict[str, Any]:
        self.evaluate_calls.append(script)
        return self._evaluate_result


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self._page = page
        self.fingerprint = None
        self.headless = None
        self.closed = False

    def new_page(self) -> FakePage:
        return self._page

    def close(self) -> None:
        self.closed = True


class FakePlaywright:
    def __enter__(self) -> FakePlaywright:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _install_fake_playwright(monkeypatch, page: FakePage) -> dict[str, Any]:
    """Patch cli.sync_playwright + stealth_context_sync; capture the call args."""

    captured: dict[str, Any] = {}
    context = FakeContext(page)

    def fake_sync_playwright() -> FakePlaywright:
        return FakePlaywright()

    def fake_stealth_context_sync(playwright, **kwargs: Any) -> FakeContext:
        captured.update(kwargs)
        context.headless = kwargs.get("headless")
        context.fingerprint = kwargs.get("fingerprint")
        return context

    monkeypatch.setattr(cli, "sync_playwright", fake_sync_playwright)
    monkeypatch.setattr(cli, "stealth_context_sync", fake_stealth_context_sync)
    captured["_context"] = context
    return captured


def test_profiles_lists_presets(capsys):
    rc = cli.main(["profiles"])
    out = capsys.readouterr().out
    assert rc == 0
    for name in ("brave", "chrome", "edge", "firefox"):
        assert name in out


def test_profiles_json_is_parseable(capsys):
    rc = cli.main(["profiles", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["firefox"]["engine"] == "gecko"
    assert payload["chrome"]["engine"] == "chromium"


def test_check_with_preset_passes_fingerprint(monkeypatch, capsys):
    page = FakePage(
        {
            "url": "https://example.com/",
            "title": "Example",
            "webdriverType": "boolean",
            "webdriverValue": "false",
            "userAgent": "ua",
        }
    )
    captured = _install_fake_playwright(monkeypatch, page)

    rc = cli.main(["check", "https://example.com", "--preset", "firefox"])
    out = capsys.readouterr().out

    assert rc == 0
    # A real FingerprintProfile was applied for the firefox preset.
    assert captured["fingerprint"] is not None
    assert captured["fingerprint"].webgl_vendor == "Mozilla"
    assert page.goto_calls[0][0] == "https://example.com"
    assert "navigator.webdriver value: false" in out
    assert captured["_context"].closed is True


def test_check_creepjs_uses_creepjs_url_and_parses_signals(monkeypatch, capsys):
    page = FakePage(
        {
            "url": cli.CREEPJS_URL,
            "title": "CreepJS",
            "trust": "72.5% (high)",
            "lies": "0",
            "fingerprintId": "abc123",
            "bot": "false",
            "rawLength": 4096,
        }
    )
    _install_fake_playwright(monkeypatch, page)

    rc = cli.main(["check", "--creepjs"])
    out = capsys.readouterr().out

    assert rc == 0
    # No URL argument was given; --creepjs resolved the target itself.
    assert page.goto_calls[0][0] == cli.CREEPJS_URL
    assert page.goto_calls[0][1]["wait_until"] == "networkidle"
    assert "trust score: 72.5% (high)" in out
    assert "lies: 0" in out


def test_check_creepjs_json_output(monkeypatch, capsys):
    page = FakePage({"url": cli.CREEPJS_URL, "trust": "90% (high)", "lies": "1"})
    _install_fake_playwright(monkeypatch, page)

    rc = cli.main(["check", "--creepjs", "--json"])
    out = capsys.readouterr().out

    assert rc == 0
    payload = json.loads(out)
    assert payload["trust"] == "90% (high)"


def test_check_without_url_or_creepjs_errors(monkeypatch, capsys):
    # No browser should be launched in this path; patch to fail loudly if it is.
    def explode(*_a: object, **_k: object) -> None:
        raise AssertionError("playwright must not launch without a target")

    monkeypatch.setattr(cli, "sync_playwright", explode)

    rc = cli.main(["check"])
    out = capsys.readouterr().out
    assert rc == 2
    assert "Provide a URL" in out


def test_check_timeout_returns_exit_code_two(monkeypatch, capsys):
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    page = FakePage({})

    def boom(url: str, **kwargs: Any) -> None:
        raise PlaywrightTimeoutError("nav timeout")

    page.goto = boom  # type: ignore[method-assign]
    captured = _install_fake_playwright(monkeypatch, page)

    rc = cli.main(["check", "https://example.com"])
    out = capsys.readouterr().out
    assert rc == 2
    assert "Timed out" in out
    assert captured["_context"].closed is True


def test_format_creepjs_signals_is_pure():
    text = cli.format_creepjs_signals({"trust": "50% (low)", "lies": "3", "url": "u"})
    assert "trust score: 50% (low)" in text
    assert "lies: 3" in text


def test_collect_creepjs_signals_uses_scrape_script():
    page = FakePage({"trust": "x"})
    result = cli.collect_creepjs_signals(page)
    assert result == {"trust": "x"}
    assert page.evaluate_calls == [cli.CREEPJS_SCRAPE_SCRIPT]


def test_build_parser_preset_choices_match_presets():
    parser = cli.build_parser()
    # Parsing an unknown preset should fail argument validation.
    with pytest.raises(SystemExit):
        parser.parse_args(["check", "https://example.com", "--preset", "safari"])
