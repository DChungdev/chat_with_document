import logging
from typing import Any

import pytest

from docchat_core.config import AppConfig, Settings


class FakeStore:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values
        self.calls = 0
        self.fail = False

    async def load_all(self) -> dict[str, Any]:
        self.calls += 1
        if self.fail:
            raise ConnectionError("db down")
        return dict(self.values)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def test_flag_change_takes_effect_after_ttl() -> None:
    store, clock = FakeStore({"qa_enabled": True}), Clock()
    cfg = AppConfig(store, ttl_seconds=30, clock=clock)
    assert await cfg.qa_enabled() is True
    store.values["qa_enabled"] = False
    clock.now = 10
    assert await cfg.qa_enabled() is True  # còn trong TTL
    clock.now = 31
    assert await cfg.qa_enabled() is False
    assert store.calls == 2


async def test_invalidate_forces_reload() -> None:
    store = FakeStore({"qa_enabled": True})
    cfg = AppConfig(store, clock=Clock())
    await cfg.qa_enabled()
    store.values["qa_enabled"] = False
    cfg.invalidate()
    assert await cfg.qa_enabled() is False


async def test_missing_key_uses_default_and_warns_once(caplog: pytest.LogCaptureFixture) -> None:
    cfg = AppConfig(FakeStore({}), clock=Clock())
    with caplog.at_level(logging.WARNING):
        assert await cfg.max_file_size_bytes() == 20 * 1024 * 1024
        assert await cfg.max_file_size_bytes() == 20 * 1024 * 1024
    warnings = [r for r in caplog.records if "missing" in r.getMessage()]
    assert len(warnings) == 1


async def test_typed_values_come_from_store() -> None:
    cfg = AppConfig(FakeStore({"max_question_length": "1500", "retrieval_min_score": 0.5}))
    assert await cfg.max_question_length() == 1500
    assert await cfg.retrieval_min_score() == 0.5


async def test_serves_stale_values_when_store_fails_after_first_load() -> None:
    store, clock = FakeStore({"qa_enabled": False}), Clock()
    cfg = AppConfig(store, ttl_seconds=1, clock=clock)
    assert await cfg.qa_enabled() is False
    store.fail, clock.now = True, 5
    assert await cfg.qa_enabled() is False


async def test_first_load_failure_propagates() -> None:
    store = FakeStore({})
    store.fail = True
    with pytest.raises(ConnectionError):
        await AppConfig(store).qa_enabled()


def test_settings_safe_dump_hides_secrets() -> None:
    s = Settings(jwt_secret="top-secret", s3_secret_key="s3-secret")  # type: ignore[arg-type]
    dump = s.safe_dump()
    flat = str(dump)
    assert "top-secret" not in flat and "s3-secret" not in flat
    assert "docchat_dev" not in flat  # mật khẩu trong URL CSDL
    assert dump["environment"] == "dev"
    assert "top-secret" not in repr(s)
