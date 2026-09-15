# Inventory Module

Inventory owns offices, audiences, their equipment grids, hardware files,
specification templates and hardware analytics. It remains part of the same
application and PostgreSQL database as identity.

## Responsibilities

- `application/`: use cases, permissions, audit calls and event results.
- `ports.py` and `contracts.py`: typed service interfaces and operation results.
- `schemas/` and `types.py`: validation and DTOs without SQLAlchemy dependencies.
- `services/`: inventory rules, grid synchronization and DTO conversion.
- `repositories/` and `models/`: persistence owned by inventory.
- `adapters/`: event delivery, file storage and public directory readers.
- `public.py`: read-only audience/office context for other business modules.

FastAPI dependencies wire concrete implementations. Notifications consume
`AudienceDirectory` and `OfficeDirectory`, not repositories or live ORM rows.
The directory adapters return only the fields notifications need. Other modules
must not import inventory services, repositories or models for business logic.

Service methods called by use cases return DTOs. Internal grid operations may
share ORM entities within inventory and the same transaction; there is no extra
domain entity hierarchy duplicating SQLAlchemy models. Shared storage and Redis
infrastructure remain outside inventory.

## Transactions

Repositories flush but do not commit or roll back. Cache invalidation uses an
explicit post-commit callback injected by the composition layer, without looking
for `repo.db` or `repo.session`. Office/filter cache population also runs after
commit with copied DTOs. Rollback discards pending cache writes and invalidation.
Redis remains a best-effort cache with a TTL, not a distributed transaction.

HTTP schemas, UUID routing, table names, enum labels and constraints are unchanged
by the module move. Registry tests check foreign keys and import order; runtime
tests cover nested DTOs and post-commit behavior. OpenAPI and compiled PostgreSQL
DDL were compared before and after this refactor.

## Remaining Work

The global registry still loads inventory and identity alongside audit and
notification models. Bootstrap now uses inventory's provisioning service and
repository through a public contract. Explicit office IDs are protected by a
table lock; sequence synchronization never rewinds an existing sequence.
Sequence advancement can leave gaps after rollback, but cannot undo a user's
data or force the next generated ID onto an existing seeded row.

Object storage is not transactional: deleting a file before a DB rollback and
cleaning uploads after failed transactions still require dedicated lifecycle
handling. This refactor isolates storage code but does not claim to solve it.
