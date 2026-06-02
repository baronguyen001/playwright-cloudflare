from pw_stealth import UA_POOL, VIEWPORTS, Fingerprint, random_fingerprint


def test_random_fingerprint_is_deterministic_with_seed():
    assert random_fingerprint(seed=1) == random_fingerprint(seed=1)


def test_random_fingerprint_has_expected_fields():
    fp = random_fingerprint(seed=2)
    assert isinstance(fp, Fingerprint)
    assert fp.user_agent in UA_POOL
    assert fp.viewport in VIEWPORTS
    assert fp.locale
    assert fp.timezone_id
