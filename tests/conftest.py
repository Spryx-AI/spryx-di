import pytest

from spryx_di import Container


@pytest.fixture
def container() -> Container:
    return Container()
