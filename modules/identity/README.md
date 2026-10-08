# Identity Module

Identity owns users, credentials, sessions and refresh rotation.
It is part of a modular monolith, not a separately deployed service.

## Structure

- `application/`: use cases, authorization rules, audit calls and event results.
- `ports.py`: dependencies required by use cases.
- `contracts.py`: plain internal result objects; no ORM state.
- `public.py`: data-only interface consumed by other business modules.
- `schemas/`: request and response validation, independent of persistence.
- `roles.py`: the shared identity role enum, independent of SQLAlchemy.
- `services/`: internal operations composing repositories, hashing and adapters.
- `repositories/`: SQL queries and flushes, without commit, caching or hashing.
- `models/`: identity-owned SQLAlchemy tables.
- `adapters/`: Redis profile cache, avatar storage, SSE authorization and event delivery.

Use cases depend on ports. Concrete services and adapters are wired in
`dependencies/`, the FastAPI composition layer. Internal services are not a
second public API: their ORM objects, especially session records, stay inside
identity. No generic repository hierarchy or duplicate domain entity layer is
required for these operations.

## Boundaries

Other business modules import `modules.identity.public`, not identity services,
repositories or ORM models. Notifications receive the `UserDirectory` protocol;
their service does not query identity tables directly. HTTP adapters may import
identity request/response schemas and application results.

User reads return `UserOut` or `AuthenticatedUser`. Password hashes are only
available through the internal `UserCredentials` contract. Authentication reads
current roles and token version from PostgreSQL, never from the profile cache.

## Transactions And Cache

Repositories flush but never commit. The request transaction completes before
the HTTP response; application use cases may explicitly commit security changes
that must survive an error response, such as refresh-token reuse revocation.

Cache population and invalidation are scheduled through the injected post-commit
callback. Rollback discards both. Population captures a DTO, not a live ORM
instance. Redis remains best-effort with a bounded TTL, not an authority for
permissions. This does not provide distributed transactional cache consistency.

Model declarations import `db.orm.Base` and `db.mixins`. Application sessions and
Alembic load the complete registry through `db.base`. Moving Python files does
not change table names, foreign keys or PostgreSQL enum labels.

## Remaining Migration Work

Notifications now owns its models, repositories, schemas and services and exposes
a public delivery contract. Inventory exposes read-only directory contracts to
notifications. Administration now owns audit and reads identity through public summaries;
the shared model registry still aggregates the module models.

Operational user creation and password reset now live in ManagedUserService.
CLI entry points only parse arguments and invoke services assembled by
management.runtime. Bootstrap consumes public provisioning contracts. Password
reset increments the access-token version atomically, revokes refresh sessions
in the same transaction and schedules cache invalidation after commit.

Замена аватара использует callbacks commit/rollback, внедряемые через
`dependencies/`. Старый файл удаляется только после подтвержденного commit,
новая загрузка удаляется при rollback до начала COMMIT. При ошибке или отмене
во время COMMIT оба файла сохраняются: ссылка в БД могла уже измениться.
Неопределенный исход записывается в журнал; перед очисткой проверьте ссылки
на файлы в БД. Очистка не маскирует исходную ошибку транзакции.
Это не распределенная транзакция: сбой процесса или хранилища может оставить
лишний объект, поэтому ошибки callbacks записываются в журнал.

Architecture tests enforce the identity application, repository and public
boundaries. Registry tests start fresh interpreters to detect import cycles.
