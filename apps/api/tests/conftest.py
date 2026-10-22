from collections.abc import Iterator

import pytest
from api_helpers import Env, make_env


@pytest.fixture()
def env() -> Iterator[Env]:
    yield from make_env()
