## ADDED Requirements

### Requirement: Zensical configuration
The project SHALL have a `zensical.toml` at the root with site name, description, author, repo URL, theme, i18n (en default + pt), and nav structure.

#### Scenario: Config file exists and is valid
- **WHEN** `zensical.toml` exists at project root
- **THEN** it SHALL contain project metadata, theme config, i18n with en (default) and pt languages, and complete nav structure

### Requirement: Docs directory structure
The project SHALL have `docs/en/` and `docs/pt/` directories with identical file structure.

#### Scenario: Parallel directory structure
- **WHEN** a file exists at `docs/en/concepts/modules.md`
- **THEN** a corresponding file SHALL exist at `docs/pt/concepts/modules.md`

### Requirement: GitHub Pages CI workflow
The project SHALL have `.github/workflows/docs.yml` that builds and deploys docs on push to main.

#### Scenario: Docs deploy on push
- **WHEN** changes to `docs/**` or `zensical.toml` are pushed to main
- **THEN** the workflow SHALL run `zensical build` and deploy to GitHub Pages

### Requirement: Dev dependency
The project SHALL include `zensical` as an optional dependency under `[project.optional-dependencies] docs`.

#### Scenario: Install docs tooling
- **WHEN** `pip install spryx-di[docs]` is run
- **THEN** zensical SHALL be installed
