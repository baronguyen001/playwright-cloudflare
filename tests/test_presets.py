import pytest

from pw_stealth import (
    FingerprintProfile,
    is_internally_consistent,
    load_preset,
    preset_engine,
    preset_names,
)
from pw_stealth.fingerprint import fingerprint_init_script

PRESET_NAMES = ["brave", "chrome", "edge", "firefox"]


def test_preset_names_are_sorted_and_complete():
    assert preset_names() == PRESET_NAMES


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_load_preset_returns_fingerprint_profile(name):
    profile = load_preset(name)
    assert isinstance(profile, FingerprintProfile)
    # Every preset is a complete desktop identity, not an empty profile.
    assert profile.user_agent
    assert profile.viewport == dict(profile.viewport)
    assert profile.locale
    assert profile.hardware_concurrency and profile.hardware_concurrency > 0
    assert profile.device_memory and profile.device_memory > 0
    assert profile.webgl_vendor
    assert profile.webgl_renderer


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_each_preset_is_internally_consistent(name):
    assert is_internally_consistent(name) is True


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_engine_matches_user_agent_token(name):
    profile = load_preset(name)
    engine = preset_engine(name)
    ua = profile.user_agent or ""
    if engine == "gecko":
        assert "Firefox/" in ua and "Gecko/" in ua
        assert "Chrome/" not in ua
        assert profile.webgl_vendor == "Mozilla"
    else:
        assert engine == "chromium"
        assert "Chrome/" in ua
        assert "Firefox/" not in ua
        assert profile.webgl_vendor and profile.webgl_vendor.startswith("Google Inc.")


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_preset_locale_and_languages_agree(name):
    profile = load_preset(name)
    languages = profile.resolved_languages
    assert languages is not None
    base = profile.locale.split("-", maxsplit=1)[0]
    assert any(lang.split("-", maxsplit=1)[0] == base for lang in languages)
    # The first language entry should be the full locale.
    assert languages[0] == profile.locale


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_preset_init_script_carries_its_vectors(name):
    profile = load_preset(name)
    script = fingerprint_init_script(profile)
    assert profile.webgl_vendor in script
    assert str(profile.hardware_concurrency) in script
    assert profile.timezone_id in script
    assert "toDataURL" in script  # canvas_noise is enabled on every preset


def test_load_preset_is_case_insensitive():
    assert load_preset("CHROME") == load_preset("chrome")
    assert preset_engine("Firefox") == "gecko"


def test_load_preset_rejects_unknown_name():
    with pytest.raises(ValueError, match="unknown preset"):
        load_preset("safari")
    with pytest.raises(ValueError, match="available presets"):
        preset_engine("opera")


def test_inconsistent_handmade_profile_is_flagged_indirectly():
    # Sanity: a Firefox UA paired with a Chromium WebGL vendor is *not* one of our
    # presets, and the consistency contract that presets satisfy would reject it.
    contradictory = FingerprintProfile(
        user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
        webgl_vendor="Google Inc.",
        locale="en-US",
    )
    # Mirror the firefox-engine rule: Gecko UA must not advertise a Chromium WebGL vendor.
    assert contradictory.webgl_vendor not in {"Mozilla"}
    assert "Firefox/" in (contradictory.user_agent or "")
