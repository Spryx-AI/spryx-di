## Context

A Spryx utiliza uma arquitetura modular monolith onde cada modulo (identity, conversations, billing) registra seus proprios servicos. Atualmente o wiring e feito manualmente, sem container centralizado. A biblioteca `spryx-di` sera um pacote standalone, type-safe, com zero dependencias runtime, projetado para funcionar perfeitamente com a toolchain Astral (uv, ty, ruff).

O design spec original define a API publica completa, algoritmo de resolucao, e integracao com FastAPI. O nome do pacote e `spryx-di` (import: `spryx_di`).

## Goals / Non-Goals

**Goals:**
- Container de DI com API minima: register, singleton, instance, factory, resolve
- Auto-wiring via `__init__` type hints com deteccao de dependencia circular
- Type safety completa — funcionar com ty (Astral) sem erros, usar generics e overloads onde necessario
- Scoped containers para dependencias request-level
- Sistema de modulos para composicao de aplicacoes modulares
- Integracao FastAPI opcional (Inject, ScopedInject, configure, middleware)
- Integracao pydantic-settings opcional para resolver BaseSettings como dependencias
- Cobertura de testes unitarios completa
- Toolchain: uv (package management), ty (type checking), ruff (lint/format)

**Non-Goals:**
- Decorators de injecao no codigo de dominio
- Resolucao async (init e sync em Python)
- Auto-discovery / classpath scanning
- Named dependencies (tipos sao a unica chave)
- Hierarquias de container alem de 1 nivel (parent → scope)
- Thread-safety guarantees (target e async single-threaded)

## Decisions

### D1: Estrutura do pacote — src layout com uv

**Decisao**: Usar `src/spryx_di/` layout gerenciado por uv com pyproject.toml.

**Alternativas**: Flat layout (`spryx_di/` na raiz). Rejeitado porque src layout previne imports acidentais do diretorio local durante testes e e o padrao recomendado para bibliotecas.

### D2: Type checking com ty em vez de mypy

**Decisao**: Usar ty (Astral) como type checker primario, com configuracao strict. Incluir `py.typed` marker.

**Alternativas**: mypy (mais maduro, mas mais lento e nao faz parte da toolchain Astral). A escolha de ty alinha com o ecossistema uv/ruff e e significativamente mais rapido.

**Implicacoes**: Usar `typing` moderno (Python 3.11+), generics com `type[T]`, `TypeVar`, e `overload` onde necessario para que ty infira tipos corretamente nos call sites.

### D3: Container usa dicionarios internos por tipo de registro

**Decisao**: O Container mantem 4 dicionarios internos:
- `_instances: dict[type, Any]` — instancias pre-construidas
- `_factories: dict[type, Callable]` — factory functions
- `_singletons: dict[type, type]` — mapeamento interface→impl (singleton)
- `_transients: dict[type, type]` — mapeamento interface→impl (transient)
- `_singleton_cache: dict[type, Any]` — cache de singletons resolvidos

**Alternativas**: Um unico dicionario com enum de lifecycle. Rejeitado por adicionar indirection e complicar type inference.

### D4: Algoritmo de resolucao com stack para deteccao circular

**Decisao**: Resolve usa uma stack (set) de tipos em resolucao. Se um tipo aparece duas vezes, levanta `CircularDependencyError` com a cadeia completa. A stack e passada como parametro interno (nao thread-local).

### D5: FastAPI integration como submodulo opcional

**Decisao**: `spryx_di.ext.fastapi` contem Inject, ScopedInject, configure. So importavel quando fastapi esta instalado. Definido como optional extra no pyproject.toml: `pip install spryx-di[fastapi]`.

**Alternativas**: Pacote separado (`spryx-di-fastapi`). Rejeitado por fragmentar o projeto sem beneficio real — o submodulo so e importado se FastAPI esta presente.

### D6: pydantic-settings integration como submodulo opcional

**Decisao**: `spryx_di.ext.settings` fornece um helper `register_settings(container, SettingsClass)` que registra uma instancia de BaseSettings como singleton. Optional extra: `pip install spryx-di[settings]`.

### D7: Testing utilities no submodulo testing

**Decisao**: `spryx_di.testing` exporta `override()` context manager que faz backup dos registros, aplica overrides, e restaura ao sair. Sem dependencias extras.

### D8: Ruff para lint e format, sem ferramentas adicionais

**Decisao**: Ruff substitui black, isort, flake8. Configuracao no pyproject.toml com `line-length = 100`, `target-version = "py311"`.

## Risks / Trade-offs

- **[ty ainda em desenvolvimento]** → ty pode ter gaps de cobertura vs mypy. Mitigacao: manter testes de tipo como parte do CI, reportar bugs upstream.
- **[Generics complexos para type safety]** → Overloads e TypeVar podem complicar o codigo interno do container. Mitigacao: manter API publica simples, complexidade generics fica interna.
- **[Zero dependencias runtime limita funcionalidade]** → Nao podemos usar helpers de terceiros. Mitigacao: a stdlib de Python 3.11+ tem `typing`, `inspect`, `dataclasses` que cobrem tudo necessario.
- **[ScopedContainer heranca vs composicao]** → Scope herda do parent via referencia, nao copia. Se o parent for mutado apos criar o scope, o scope ve as mudancas. Mitigacao: documentar comportamento; na pratica containers sao configurados no startup e nao mutados depois.
