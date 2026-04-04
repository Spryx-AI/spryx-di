## Context

spryx-di e uma lib Python standalone com zero deps. Precisa de documentacao bilingual (en/pt) hospedada no GitHub Pages. A ferramenta escolhida e Zensical com i18n nativo.

## Goals / Non-Goals

**Goals:**
- Docs completas em ingles (fonte de verdade) e portugues (traducao)
- Deploy automatico no GitHub Pages via CI
- Estrutura progressiva: Getting Started -> Concepts -> Guides -> API Reference
- Todos os exemplos executaveis (copiar/colar funciona)

**Non-Goals:**
- Documentacao de API gerada automaticamente (autodoc) — manual e mais claro pra lib pequena
- Versioning de docs (v0.1, v0.2) — uma versao so por enquanto
- Blog ou seção de tutoriais em video

## Decisions

### D1: Zensical como gerador de docs
Zensical com suporte a i18n nativo. Estrutura de pastas paralelas `docs/en/` e `docs/pt/`.

### D2: Ingles como fonte de verdade
Todo conteudo novo em `docs/en/` primeiro. `docs/pt/` e sempre traducao. Blocos de codigo nao sao traduzidos.

### D3: Paginas que nao precisam de traducao
`changelog.md`, `contributing.md` e `api/*.md` podem ficar so em ingles. Conteudo tecnico versionado.

### D4: CI com GitHub Pages
Workflow `.github/workflows/docs.yml` roda `zensical build` e faz deploy com `peaceiris/actions-gh-pages@v4`. Trigga em push para main quando `docs/**` ou `zensical.toml` mudam.

## Risks / Trade-offs

- **[Zensical pode ter limitacoes]** → Se faltar feature, Zensical suporta muitas features do Material for MkDocs nativamente
- **[Manutencao de traducao]** → Traducao pode ficar desatualizada. Mitigacao: workflow com Claude Code pra traduzir em batch
