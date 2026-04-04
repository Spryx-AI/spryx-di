from __future__ import annotations

from spryx_di import Container
from spryx_di.testing import override


class TeamReader:
    pass


class PgTeamReader(TeamReader):
    pass


class FakeTeamReader(TeamReader):
    pass


class TestOverrideContextManager:
    def test_override_and_restore(self, container: Container) -> None:
        container.singleton(TeamReader, PgTeamReader)

        with override(container, {TeamReader: FakeTeamReader}):
            result = container.resolve(TeamReader)
            assert isinstance(result, FakeTeamReader)

        result = container.resolve(TeamReader)
        assert isinstance(result, PgTeamReader)

    def test_override_with_instance(self, container: Container) -> None:
        container.singleton(TeamReader, PgTeamReader)
        fake = FakeTeamReader()

        with override(container, {TeamReader: fake}):
            result = container.resolve(TeamReader)
            assert result is fake

        result = container.resolve(TeamReader)
        assert isinstance(result, PgTeamReader)
