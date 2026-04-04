## ADDED Requirements

### Requirement: register_settings helper
The system SHALL provide `register_settings(container, settings_class)` that instantiates a `pydantic-settings` `BaseSettings` subclass and registers it as a singleton instance.

#### Scenario: Register and resolve settings
- **WHEN** `register_settings(container, AppSettings)` is called where `AppSettings` is a `BaseSettings` subclass
- **THEN** `container.resolve(AppSettings)` SHALL return a singleton `AppSettings` instance loaded from environment

### Requirement: Settings as dependency in auto-wiring
The system SHALL allow auto-wired classes to depend on registered settings types.

#### Scenario: Service depends on settings
- **WHEN** `Service.__init__(self, settings: AppSettings)` and `AppSettings` is registered via `register_settings`
- **THEN** `container.resolve(Service)` SHALL inject the `AppSettings` instance

### Requirement: register_settings is importable from ext.settings
The helper SHALL be importable as `from spryx_di.ext.settings import register_settings`.

#### Scenario: Import path works
- **WHEN** pydantic-settings is installed and `from spryx_di.ext.settings import register_settings` is executed
- **THEN** the import SHALL succeed without errors
