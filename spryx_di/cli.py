from __future__ import annotations

import importlib
from typing import Annotated

import typer

from spryx_di.analysis import analyze
from spryx_di.module import ApplicationContext, _normalize_provider

app = typer.Typer(name="spryx-di", no_args_is_help=True)


def _read_config() -> str | None:
    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        return config.get("tool", {}).get("spryx-di", {}).get("app")
    except FileNotFoundError:
        return None


def _load_context(app_path: str) -> ApplicationContext:
    module_path, _, func_name = app_path.rpartition(":")
    if not module_path or not func_name:
        typer.echo(
            f"Error: Invalid app path '{app_path}'. Expected format: module.path:function_name"
        )
        raise typer.Exit(1)
    try:
        mod = importlib.import_module(module_path)
    except ImportError as e:
        typer.echo(f"Error: Could not import '{module_path}': {e}")
        raise typer.Exit(1) from None
    func = getattr(mod, func_name, None)
    if func is None:
        typer.echo(f"Error: '{module_path}' has no attribute '{func_name}'")
        raise typer.Exit(1)
    ctx = func()
    if not isinstance(ctx, ApplicationContext):
        typer.echo(
            f"Error: '{app_path}' returned {type(ctx).__name__}, expected ApplicationContext"
        )
        raise typer.Exit(1)
    return ctx


def _resolve_context(app_path: str | None) -> ApplicationContext:
    path = app_path or _read_config()
    if path is None:
        typer.echo(
            "Error: No app path provided.\n\n"
            "  Use --app flag:\n"
            "    spryx-di check --app my_app.compose:create_app_context\n\n"
            "  Or configure in pyproject.toml:\n"
            "    [tool.spryx-di]\n"
            '    app = "my_app.compose:create_app_context"'
        )
        raise typer.Exit(1)
    return _load_context(path)


AppOption = Annotated[
    str | None, typer.Option("--app", help="App context factory (module:function)")
]


@app.command()
def check(app_path: AppOption = None) -> None:
    """Run module analysis and report warnings."""
    ctx = _resolve_context(app_path)

    total_providers = sum(len(m.providers) for m in ctx._modules)
    typer.echo("spryx-di module analysis")
    typer.echo("========================\n")
    typer.echo(f"Scanning... {len(ctx._modules)} modules, {total_providers} providers\n")

    warnings = analyze(ctx)
    if warnings:
        typer.echo(f"Warnings ({len(warnings)}):")
        for w in warnings:
            typer.echo(f"  ⚠ {w}")
        raise typer.Exit(1)
    else:
        typer.echo("✓ No warnings found.")


@app.command()
def info(app_path: AppOption = None) -> None:
    """Show module composition summary."""
    ctx = _resolve_context(app_path)

    total_providers = sum(len(m.providers) for m in ctx._modules)
    total_exports = len(ctx._export_registry)
    total_deps = sum(len(m.dependencies) for m in ctx._modules)

    typer.echo("spryx-di module summary")
    typer.echo("=======================\n")
    typer.echo(f"Modules: {len(ctx._modules)}")
    typer.echo(f"Total providers: {total_providers}")
    typer.echo(f"Total exports: {total_exports}")
    typer.echo(f"Total dependencies: {total_deps}\n")

    for module in ctx._modules:
        exports = [
            _normalize_provider(p).provide.__name__
            for p in module.providers
            if _normalize_provider(p).export
        ]
        publics = [
            _normalize_provider(p).provide.__name__
            for p in module.providers
            if _normalize_provider(p).public
        ]
        typer.echo(
            f"{module.name} "
            f"({len(module.providers)} providers, "
            f"{len(exports)} exports, "
            f"{len(module.dependencies)} dependencies)"
        )
        if exports:
            typer.echo(f"  exports: {', '.join(exports)}")
        if module.dependencies:
            dep_names = ", ".join(d.__name__ for d in module.dependencies)
            typer.echo(f"  dependencies: {dep_names}")
        if publics:
            typer.echo(f"  public: {', '.join(publics)}")
        typer.echo()


@app.command()
def graph(app_path: AppOption = None) -> None:
    """Generate Mermaid dependency graph."""
    ctx = _resolve_context(app_path)

    typer.echo("graph LR")
    for module in ctx._modules:
        for dep_type in module.dependencies:
            source_module = ctx._export_registry.get(dep_type)
            if source_module:
                typer.echo(f"  {module.name} -->|{dep_type.__name__}| {source_module}")


if __name__ == "__main__":
    app()
