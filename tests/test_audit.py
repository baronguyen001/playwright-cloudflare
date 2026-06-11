from __future__ import annotations

import json
from typing import Any

from pw_stealth import audit, cli


def _signals(webdriver: str = "undefined") -> dict[str, Any]:
    return {
        "page": {"url": "https://example.com/", "title": "Example Domain"},
        "navigator": {
            "webdriverPresent": True,
            "webdriverType": webdriver,
            "webdriverValue": None,
            "webdriverString": webdriver,
            "pluginsLength": 5,
            "mimeTypesLength": 2,
            "language": "en-US",
            "languages": ["en-US", "en"],
            "userAgent": "Mozilla/5.0",
            "platform": "Win32",
            "hardwareConcurrency": 8,
            "deviceMemory": 8,
        },
        "timezone": {"name": "America/New_York", "offsetMinutes": 300},
        "webgl": {"vendor": "Google Inc.", "renderer": "ANGLE"},
        "canvas": {"available": True, "dataUrlHash": "1234", "dataUrlLength": 512},
    }


def test_audit_report_json_contains_key_signals(tmp_path):
    report = audit.build_audit_report(
        requested_url="https://example.com",
        preset="chrome",
        signals=_signals(),
        creepjs={"trust": "90% (high)", "lies": "0"},
    )
    output = tmp_path / "audit.json"

    audit.write_report(report, output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["signals"]["navigator"]["webdriverString"] == "undefined"
    assert payload["signals"]["navigator"]["pluginsLength"] == 5
    assert payload["signals"]["webgl"]["vendor"] == "Google Inc."
    assert payload["signals"]["canvas"]["dataUrlHash"] == "1234"
    assert payload["signals"]["timezone"]["name"] == "America/New_York"
    assert payload["creepjs"]["lies"] == "0"


def test_compare_reports_detects_planted_regression():
    baseline = audit.build_audit_report(
        requested_url="https://example.com",
        signals=_signals("undefined"),
    )
    current = audit.build_audit_report(
        requested_url="https://example.com",
        signals=_signals("true"),
    )

    diffs = audit.compare_reports(current, baseline)

    assert {
        "path": "signals.navigator.webdriverString",
        "baseline": "undefined",
        "current": "true",
    } in diffs
    assert "signals.navigator.webdriverString" in audit.format_diffs(diffs)


def test_audit_cli_writes_json_and_returns_nonzero_on_compare_diff(
    monkeypatch,
    tmp_path,
    capsys,
):
    baseline = audit.build_audit_report(
        requested_url="https://example.com",
        signals=_signals("undefined"),
    )
    current = audit.build_audit_report(
        requested_url="https://example.com",
        signals=_signals("true"),
    )
    baseline_path = tmp_path / "baseline.json"
    output_path = tmp_path / "current.json"
    audit.write_report(baseline, baseline_path)

    monkeypatch.setattr(cli, "run_audit_sync", lambda *args, **kwargs: current)

    rc = cli.main(
        [
            "audit",
            "https://example.com",
            "--json",
            str(output_path),
            "--compare",
            str(baseline_path),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 1
    assert json.loads(output_path.read_text(encoding="utf-8")) == current
    assert "Audit regression detected" in out
    assert "signals.navigator.webdriverString" in out


def test_collect_audit_signals_uses_audit_script():
    class FakePage:
        def __init__(self) -> None:
            self.evaluate_calls: list[str] = []

        def evaluate(self, script: str) -> dict[str, str]:
            self.evaluate_calls.append(script)
            return {"ok": "yes"}

    page = FakePage()
    result = audit.collect_audit_signals(page)

    assert result == {"ok": "yes"}
    assert page.evaluate_calls == [audit.AUDIT_SCRIPT]
