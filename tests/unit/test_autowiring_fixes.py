from __future__ import annotations

import contextlib
import sys
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from unittest.mock import patch

import pytest

from spryx_di import Container, UnresolvableTypeError

# ── TYPE_CHECKING namespace enrichment ──────────────────────���────────


class _Dep:
    pass


class _Consumer:
    def __init__(self, dep: _Dep) -> None:
        self.dep = dep


class TestTypeCheckingImports:
    def test_resolves_when_get_type_hints_fails_but_type_is_registered(
        self, container: Container
    ) -> None:
        container.instance(_Dep, _Dep())
        container.register(_Consumer, _Consumer)

        original = sys.modules["typing"].get_type_hints
        call_count = 0

        def failing_then_ok(obj, globalns=None, localns=None, include_extras=False):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and globalns is None:
                raise NameError("name '_Dep' is not defined")
            return original(obj, globalns=globalns, localns=localns, include_extras=include_extras)

        with patch("typing.get_type_hints", side_effect=failing_then_ok):
            result = container.resolve(_Consumer)

        assert isinstance(result, _Consumer)
        assert isinstance(result.dep, _Dep)

    def test_name_collision_logs_warning(
        self, container: Container, caplog: pytest.LogCaptureFixture
    ) -> None:
        FakeType = type("_Dep", (), {"__module__": "fake"})

        container.instance(_Dep, _Dep())
        container.instance(FakeType, FakeType())

        original_gth = sys.modules["typing"].get_type_hints

        def always_fail(obj, globalns=None, localns=None, include_extras=False):
            if globalns is None:
                raise NameError("simulated failure")
            return original_gth(
                obj, globalns=globalns, localns=localns, include_extras=include_extras
            )

        with (
            patch("typing.get_type_hints", side_effect=always_fail),
            caplog.at_level("WARNING", logger="spryx_di"),
            contextlib.suppress(Exception),
        ):
            container.resolve(_Consumer)


# ── Optional / Union unwrap ──────────────────────────────────────────


class _RedisPublisher:
    pass


class _ServiceWithOptional:
    def __init__(self, publisher: _RedisPublisher | None = None) -> None:
        self.publisher = publisher


class _ServiceWithRequiredOptional:
    def __init__(self, publisher: _RedisPublisher | None) -> None:
        self.publisher = publisher


class _ServiceWithPlainDep:
    def __init__(self, publisher: _RedisPublisher) -> None:
        self.publisher = publisher


class TestOptionalUnwrap:
    def test_optional_with_default_resolves_when_registered(self, container: Container) -> None:
        pub = _RedisPublisher()
        container.instance(_RedisPublisher, pub)
        svc = container.resolve(_ServiceWithOptional)
        assert svc.publisher is pub

    def test_optional_with_default_uses_default_when_not_registered(
        self, container: Container
    ) -> None:
        class _UnresolvableDep:
            def __init__(self, x: int) -> None:
                self.x = x

        class _Svc:
            def __init__(self, dep: _UnresolvableDep | None = None) -> None:
                self.dep = dep

        svc = container.resolve(_Svc)
        assert svc.dep is None

    def test_optional_without_default_resolves_when_registered(self, container: Container) -> None:
        pub = _RedisPublisher()
        container.instance(_RedisPublisher, pub)
        result = container.resolve(_ServiceWithRequiredOptional)
        assert result.publisher is pub

    def test_plain_type_still_resolves(self, container: Container) -> None:
        pub = _RedisPublisher()
        container.instance(_RedisPublisher, pub)
        svc = container.resolve(_ServiceWithPlainDep)
        assert svc.publisher is pub

    def test_unwrap_optional_returns_none_for_complex_union(self) -> None:
        assert Container._unwrap_optional(str | int) is None

    def test_unwrap_optional_returns_none_for_any(self) -> None:
        import typing as _typing

        assert Container._unwrap_optional(_typing.Any) is None

    def test_unwrap_optional_returns_none_for_generic(self) -> None:
        assert Container._unwrap_optional(list[str]) is None

    def test_unwrap_optional_extracts_type_from_union_with_none(self) -> None:
        assert Container._unwrap_optional(_RedisPublisher | None) is _RedisPublisher


# ── Protocol / ABC detection ────────────────���────────────────────────


@runtime_checkable
class _MyProtocol(Protocol):
    def do_something(self) -> None: ...


class _MyABC(ABC):
    @abstractmethod
    def do_something(self) -> None: ...


class _ConcreteFromABC(_MyABC):
    def do_something(self) -> None:
        pass


class TestProtocolABCDetection:
    def test_protocol_is_not_auto_wireable(self) -> None:
        assert Container._is_auto_wireable(_MyProtocol) is False

    def test_abc_with_abstract_methods_is_not_auto_wireable(self) -> None:
        assert Container._is_auto_wireable(_MyABC) is False

    def test_concrete_class_is_auto_wireable(self) -> None:
        assert Container._is_auto_wireable(_ConcreteFromABC) is True

    def test_builtin_is_not_auto_wireable(self) -> None:
        assert Container._is_auto_wireable(str) is False
        assert Container._is_auto_wireable(int) is False

    def test_resolving_unregistered_protocol_raises(self, container: Container) -> None:
        class _NeedsProtocol:
            def __init__(self, svc: _MyProtocol) -> None:
                self.svc = svc

        with pytest.raises(UnresolvableTypeError):
            container.resolve(_NeedsProtocol)

    def test_resolving_unregistered_abc_raises(self, container: Container) -> None:
        class _NeedsABC:
            def __init__(self, svc: _MyABC) -> None:
                self.svc = svc

        with pytest.raises(UnresolvableTypeError):
            container.resolve(_NeedsABC)

    def test_registered_protocol_resolves(self, container: Container) -> None:
        class _Impl:
            def do_something(self) -> None:
                pass

        container.register(_MyProtocol, _Impl)
        result = container.resolve(_MyProtocol)
        assert isinstance(result, _Impl)

    def test_registered_abc_resolves(self, container: Container) -> None:
        container.register(_MyABC, _ConcreteFromABC)
        result = container.resolve(_MyABC)
        assert isinstance(result, _ConcreteFromABC)
