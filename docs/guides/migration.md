# Migration from Manual DI

How to migrate from a hand-wired container to spryx-di.

## Before: Manual Factory

```python
class AppContainer:
    def __init__(self, db: Database):
        self._db = db
        self._user_repo = PgUserRepository(db)
        self._user_reader = PgUserReader(self._user_repo)
        self._team_reader = PgTeamReader(db)

    def list_handler(self) -> ListHandler:
        return ListHandler(self._user_reader, self._team_reader)
```

Problems: every new dependency requires manual wiring, no boundary enforcement, hard to test.

## After: spryx-di

```python
from spryx_di import ClassProvider, ValueProvider, Module, ApplicationContext

identity_module = Module(
    name="identity",
    providers=[
        ClassProvider(provide=UserRepository, use_class=PgUserRepository),
        ClassProvider(provide=UserReader, use_class=PgUserReader),
        ClassProvider(provide=TeamReader, use_class=PgTeamReader),
    ],
    exports=[UserReader, TeamReader],
)

ctx = ApplicationContext(
    modules=[identity_module],
    globals=[ValueProvider(provide=Database, use_value=db)],
)

handler = ctx.resolve(ListHandler)  # auto-wired
```

## Migration Steps

1. **Identify modules** — group related classes by bounded context
2. **Define ports** — extract interfaces (ABCs/Protocols) for cross-module deps
3. **Create Module definitions** — one per bounded context with providers and exports
4. **Replace manual wiring** — `ApplicationContext` replaces the factory class
5. **Update tests** — use `Container` + fakes instead of hand-constructing objects
