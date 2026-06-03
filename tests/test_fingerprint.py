import pytest

from pw_stealth import (
    UA_POOL,
    VIEWPORTS,
    Fingerprint,
    FingerprintProfile,
    fingerprint_context_options,
    fingerprint_init_script,
    random_fingerprint,
)


def test_random_fingerprint_is_deterministic_with_seed():
    assert random_fingerprint(seed=1) == random_fingerprint(seed=1)


def test_random_fingerprint_has_expected_fields():
    fp = random_fingerprint(seed=2)
    assert isinstance(fp, Fingerprint)
    assert fp.user_agent in UA_POOL
    assert fp.viewport in VIEWPORTS
    assert fp.locale
    assert fp.timezone_id


def test_fingerprint_profile_context_options_are_opt_in():
    profile = FingerprintProfile(
        locale="en-GB",
        timezone_id="Europe/London",
        hardware_concurrency=8,
        device_memory=8,
        webgl_vendor="Google Inc.",
    )

    assert fingerprint_context_options(profile) == {
        "locale": "en-GB",
        "timezone_id": "Europe/London",
    }


def test_fingerprint_profile_builds_locale_timezone_and_device_script():
    profile = FingerprintProfile(
        locale="en-GB",
        timezone_id="Europe/London",
        hardware_concurrency=12,
        device_memory=8,
    )

    script = fingerprint_init_script(profile)

    assert "hardwareConcurrency" in script
    assert "deviceMemory" in script
    assert "Europe/London" in script
    assert '"en-GB"' in script
    assert '"en"' in script


def test_fingerprint_profile_webgl_and_canvas_are_opt_in():
    script = fingerprint_init_script(
        FingerprintProfile(
            webgl_vendor="Intel Inc.",
            webgl_renderer="Intel Iris OpenGL Engine",
            canvas_noise=True,
        )
    )

    assert "WebGLRenderingContext" in script
    assert "37445" in script
    assert "Intel Inc." in script
    assert "toDataURL" in script

    empty_script = fingerprint_init_script(FingerprintProfile())
    assert "WebGLRenderingContext" not in empty_script
    assert "toDataURL" not in empty_script


def test_fingerprint_profile_validates_consistency_values():
    with pytest.raises(ValueError, match="hardware_concurrency"):
        FingerprintProfile(hardware_concurrency=0)

    with pytest.raises(ValueError, match="device_memory"):
        FingerprintProfile(device_memory=0)
