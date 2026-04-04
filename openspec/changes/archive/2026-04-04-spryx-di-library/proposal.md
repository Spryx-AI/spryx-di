## Why

Python carece de um container de injecao de dependencias leve, baseado em tipos, que funcione com auto-wiring via type hints de `__init__`, integre nativamente com FastAPI `Depends()`, suporte arquiteturas modulares (modular monolith), e tenha zero dependencias runtime. As solucoes existentes estao abandonadas (lagom), sao pesadas demais (dependency-injector), ou simplesmente nao existem para o caso de uso de containers com escopo alem do request do FastAPI.

A Spryx precisa disso agora para padronizar a composicao de modulos no backend, eliminando wiring manual e garantindo type safety com a toolchain Astral (ty, ruff, uv).

## What Changes

- Criar a biblioteca `spryx-di` como pacote Python standalone com zero dependencias runtime
- `Container` com registros: `register` (transient), `singleton`, `instance`, `factory`
- Auto-wiring automatico via inspecao de `__init__` type hints com deteccao de dependencias circulares
- `ScopedContainer` que herda do parent com overrides locais
- `ModuleDefinition` e `compose_modules()` para composicao modular
- Integracao opcional com FastAPI: `Inject()`, `ScopedInject()`, `configure()`, middleware de request scope
- Integracao opcional com `pydantic-settings` para resolver configuracoes tipadas
- Utilidades de teste: `override()` context manager
- Toolchain: UV para gerenciamento de pacotes, ty para type checking, ruff para linting/formatting
- Cobertura de testes unitarios completa para validar toda funcionalidade core

## Capabilities

### New Capabilities
- `container-core`: Container de DI com register, singleton, instance, factory, resolve, e acesso via `__getitem__`
- `auto-wiring`: Resolucao automatica de dependencias via `__init__` type hints com deteccao circular
- `scoped-container`: Container com escopo que herda registros do parent e suporta overrides locais
- `module-system`: ModuleDefinition e compose_modules para composicao modular de aplicacoes
- `fastapi-integration`: Inject, ScopedInject, configure, e middleware de request scope para FastAPI
- `testing-utilities`: override context manager e container.override() para facilitar testes
- `settings-integration`: Integracao com pydantic-settings para resolver BaseSettings como dependencias tipadas

### Modified Capabilities

## Impact

- Novo pacote Python `spryx-di` publicavel no PyPI
- Dependencias de dev: uv, ty, ruff, pytest, pytest-asyncio, fastapi, httpx, pydantic-settings
- Zero dependencias runtime no core; fastapi e pydantic-settings como optional extras
- Impacta futuros projetos Spryx que adotarao este container como padrao de DI
