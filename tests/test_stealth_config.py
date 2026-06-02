from pw_stealth import STEALTH_ARGS, STEALTH_INIT_JS
from pw_stealth.stealth import _merge_args, _resolve_chrome_profile


def test_stealth_args_hide_automation_without_enable_automation():
    assert "--disable-blink-features=AutomationControlled" in STEALTH_ARGS
    assert "--enable-automation" not in STEALTH_ARGS


def test_init_script_mentions_webdriver_patch():
    assert "navigator" in STEALTH_INIT_JS
    assert "webdriver" in STEALTH_INIT_JS


def test_merge_args_filters_enable_automation_and_adds_new_headless():
    args = _merge_args(["--enable-automation", "--window-size=1366,900"], headless=True)
    assert "--enable-automation" not in args
    assert "--headless=new" in args
    assert "--window-size=1366,900" in args


def test_resolve_specific_chrome_profile_path():
    launch_dir, launch_args, channel = _resolve_chrome_profile(
        r"C:\Users\me\AppData\Local\Google\Chrome\User Data\Profile 2"
    )
    assert launch_dir.endswith(r"Google\Chrome\User Data")
    assert launch_args == ["--profile-directory=Profile 2"]
    assert channel == "chrome"
