## Why

spryx-di nao tem documentacao. A lib esta funcional mas sem docs ninguem adota — nem internamente na Spryx, nem como open-source. Precisa de docs bilingual (en/pt) com Zensical, cobrindo desde quickstart ate API reference.

## What Changes

- Setup Zensical com `zensical.toml` e estrutura `docs/en/` + `docs/pt/`
- Landing page com quick example e badges
- Getting Started: installation + quickstart (5 min pra primeira injecao)
- Core Concepts: container, providers, modules, boundaries, scopes, auto-wiring, lifecycle
- Integrations: FastAPI
- Guides: modular monolith, testing, migration, circular deps
- API Reference: container, module, provider, errors, fastapi, testing
- Changelog e Contributing
- GitHub Actions workflow para deploy no GitHub Pages
- Traducao pt-BR de todas as paginas de conceitos e guias

## Capabilities

### New Capabilities
- `docs-setup`: Zensical config, estrutura de pastas, CI workflow para GitHub Pages
- `docs-content`: Conteudo completo da documentacao em ingles e portugues

### Modified Capabilities

## Impact

- Novo diretorio `docs/` com ~40 arquivos markdown (en + pt)
- Novo `zensical.toml` na raiz
- Novo workflow `.github/workflows/docs.yml`
- Nova dependencia dev: `zensical`
- Atualizacao do `pyproject.toml` com optional dependency `docs`
