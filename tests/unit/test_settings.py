from __future__ import annotations

from pydantic_settings import BaseSettings

from spryx_di import Container
from spryx_di.ext.settings import register_settings


class AppSettings(BaseSettings):
    app_name: str = "test-app"
    debug: bool = False


class ServiceWithSettings:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings


class TestRegisterSettings:
    def test_register_and_resolve_settings(self, container: Container) -> None:
        register_settings(container, AppSettings)
        settings = container.resolve(AppSettings)
        assert isinstance(settings, AppSettings)
        assert settings.app_name == "test-app"

    def test_settings_is_singleton(self, container: Container) -> None:
        register_settings(container, AppSettings)
        a = container.resolve(AppSettings)
        b = container.resolve(AppSettings)
        assert a is b


class TestSettingsAsDependency:
    def test_service_depends_on_settings(self, container: Container) -> None:
        register_settings(container, AppSettings)
        svc = container.resolve(ServiceWithSettings)
        assert isinstance(svc.settings, AppSettings)
        assert svc.settings.app_name == "test-app"
