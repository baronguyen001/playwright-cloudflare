from pw_stealth import FingerprintProfile, apply_stealth_sync, stealth_context_sync


class InitScriptRecorder:
    def __init__(self) -> None:
        self.scripts: list[str] = []

    def add_init_script(self, script: str) -> None:
        self.scripts.append(script)


def test_apply_stealth_sync_adds_base_and_profile_scripts():
    recorder = InitScriptRecorder()
    profile = FingerprintProfile(
        locale="en-US",
        hardware_concurrency=8,
        device_memory=8,
        webgl_vendor="Google Inc.",
        webgl_renderer="ANGLE",
    )

    apply_stealth_sync(recorder, fingerprint=profile)

    assert len(recorder.scripts) == 1
    script = recorder.scripts[0]
    assert "webdriver" in script
    assert "hardwareConcurrency" in script
    assert "deviceMemory" in script
    assert "Google Inc." in script


def test_stealth_context_sync_is_exported():
    assert callable(stealth_context_sync)
