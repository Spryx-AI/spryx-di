# Commit changes following Conventional Commits

Create a commit that follows [Conventional Commits](https://www.conventionalcommits.org/) for python-semantic-release.

## Commit message format

```
<type>(<scope>): <description>
```

## Types and their release impact

| Type | Release | When to use |
|------|---------|-------------|
| `feat` | **minor** | New functionality for the user |
| `fix` | **patch** | Bug fix |
| `perf` | **patch** | Performance improvement |
| `refactor` | **patch** | Code change that neither fixes a bug nor adds a feature |
| `docs` | no release | Documentation only |
| `test` | no release | Adding or fixing tests |
| `chore` | no release | Tooling, CI, dependencies |
| `ci` | no release | CI/CD changes |
| `style` | no release | Formatting, whitespace |
| `build` | no release | Build system changes |

**BREAKING CHANGE**: Add `!` after type or include `BREAKING CHANGE:` in footer for **major** release.

```
feat!: remove deprecated compose_modules function
```

## Scope

Optional, lowercase, describes the area of change. Examples: `container`, `module`, `fastapi`, `testing`, `provider`.

## Rules

1. Run `git status` and `git diff --staged` to understand what changed
2. If nothing is staged, stage the relevant files (never use `git add -A`)
3. Pick the correct type based on what the change does, not what files changed
4. Write the description in imperative mood, lowercase, no period at the end
5. Keep the first line under 72 characters
6. Use body for additional context if needed (separated by blank line)
7. Never skip hooks (`--no-verify`)

## Examples

```
feat(module): add on_destroy lifecycle hook
fix(container): resolve singleton cache miss on scoped containers
refactor(provider): simplify Provider validation logic
test(module): add boundary enforcement tests for forward_ref
chore: pin all dependencies to exact versions
docs: add standalone example without FastAPI
```
