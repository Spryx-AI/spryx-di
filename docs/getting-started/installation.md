# Installation

## Requirements

- Python >= 3.11
- Zero runtime dependencies

## Install

=== "uv"

    ```bash
    uv add spryx-di
    ```

=== "pip"

    ```bash
    pip install spryx-di
    ```

=== "poetry"

    ```bash
    poetry add spryx-di
    ```

## Optional Extras

=== "uv"

    ```bash
    uv add spryx-di[fastapi]    # Inject(), ScopedInject(), configure()
    uv add spryx-di[settings]   # pydantic-settings integration
    ```

=== "pip"

    ```bash
    pip install spryx-di[fastapi]
    pip install spryx-di[settings]
    ```

=== "poetry"

    ```bash
    poetry add spryx-di -E fastapi
    poetry add spryx-di -E settings
    ```

## Development

```bash
git clone https://github.com/spryx-ai/spryx-di.git
cd spryx-di
make install  # installs dev deps + pre-commit hooks
make check    # lint + typecheck + tests with coverage
```
