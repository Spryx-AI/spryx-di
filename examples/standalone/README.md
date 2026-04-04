# Standalone Example (sem FastAPI)

Demonstra `spryx-di` como container de DI puro, sem framework web.

Caso de uso: sistema de processamento de pedidos com 3 modulos e boundary enforcement.

## Executar

```bash
cd examples/standalone
python -m app.main
```

## O que demonstra

- `Module`, `Provider`, `Scope` — definicao declarativa
- `ApplicationContext` — composicao com boundary enforcement
- `forward_ref` — dependencia bidirecional entre identity e notifications
- `resolve()` — resolucao global (sem restricoes)
- `resolve_within()` — resolucao com enforcement de fronteiras
- `ModuleBoundaryError` — erro ao violar fronteira
- Testes sem mocks — basta criar um Container com fakes
