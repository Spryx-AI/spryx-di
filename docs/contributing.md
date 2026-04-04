# Contributing

## Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone https://github.com/spryx-ai/spryx-di.git
cd spryx-di
make install
```

This installs all dev dependencies and sets up pre-commit hooks.

## Development

```bash
make check      # lint + typecheck + tests with coverage
make test       # tests with coverage
make lint       # ruff check
make format     # ruff format
make typecheck  # ty check
make docs       # serve docs locally
```

## Pre-commit Hooks

Installed automatically by `make install`. Runs on every commit:

- ruff format + lint
- ty type check
- commitlint (conventional commits)
- pygrep checks

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) with python-semantic-release:

```
feat(module): add on_destroy lifecycle hook    # triggers MINOR bump
fix(container): resolve singleton cache miss   # triggers PATCH bump
chore: update dependencies                     # no release
```

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run `make check`
5. Commit with conventional commit message
6. Open a PR against `main`
