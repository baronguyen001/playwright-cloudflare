from __future__ import annotations

from pw_stealth import pytest_plugin


class FakePage:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeContext:
    def __init__(self) -> None:
        self.scripts: list[str] = []
        self.closed = False
        self.page = FakePage()

    def add_init_script(self, script: str) -> None:
        self.scripts.append(script)

    def new_page(self) -> FakePage:
        return self.page

    def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self) -> None:
        self.context = FakeContext()

    def new_context(self) -> FakeContext:
        return self.context


def test_stealth_context_fixture_applies_init_script_and_closes():
    browser = FakeBrowser()
    fixture = pytest_plugin.stealth_context.__wrapped__(browser, None)

    context = next(fixture)
    assert "webdriver" in context.scripts[0]

    try:
        next(fixture)
    except StopIteration:
        pass

    assert context.closed is True


def test_stealth_page_fixture_yields_page_and_closes():
    context = FakeContext()
    fixture = pytest_plugin.stealth_page.__wrapped__(context)

    page = next(fixture)
    assert page is context.page

    try:
        next(fixture)
    except StopIteration:
        pass

    assert page.closed is True
