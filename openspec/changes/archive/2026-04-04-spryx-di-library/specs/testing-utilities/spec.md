## ADDED Requirements

### Requirement: override context manager
The system SHALL provide `override(container, overrides_dict)` context manager that temporarily replaces registrations and restores them on exit.

#### Scenario: Override and restore
- **WHEN** `with override(container, {TeamReader: FakeTeamReader}):` is used
- **THEN** inside the block, `container.resolve(TeamReader)` SHALL return `FakeTeamReader`
- **AND** after the block, `container.resolve(TeamReader)` SHALL return the original registration

#### Scenario: Override with instance
- **WHEN** `with override(container, {TeamReader: fake_instance})` where value is an instance (not a type)
- **THEN** the container SHALL register it as an instance for the duration of the block

### Requirement: override is importable from testing module
The override utility SHALL be importable as `from spryx_di.testing import override`.

#### Scenario: Import path works
- **WHEN** `from spryx_di.testing import override` is executed
- **THEN** the import SHALL succeed without errors
