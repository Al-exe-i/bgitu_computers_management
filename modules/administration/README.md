# Administration

The module owns audit persistence, audit query DTOs and protected-file queries.
HTTP routes enforce permissions; dependencies only assemble implementations.
The request adapter binds the authenticated actor and trusted request metadata
to the public AuditLogger contract used by identity, inventory and notifications.

Audit writes participate in the business transaction. The repository only
flushes; failures propagate to the request transaction owner. No background task,
post-commit audit write or outbox is introduced. Sensitive payload fields are
sanitized before persistence.

Reading a page loads author summaries once through identity's public
UserSummaryDirectory contract. Only ID, email, name and surname are selected.
There is no ORM relationship or model import across this boundary; the existing
user_id foreign key and ON DELETE SET NULL behavior remain unchanged.
Deleted authors serialize as null. Ordering uses created_at and ID descending.

The wire schema, table definition, filters and access rules are unchanged.
Tests cover module boundaries, import order, author batching, secret masking,
failure propagation and repository transaction ownership.

BootstrapUseCase coordinates public identity and inventory provisioning
contracts under a transaction-scoped advisory lock. CLI composition owns
commit/rollback and runs cache callbacks only after a successful commit.
Existing superusers are never changed and regular users are never promoted by
bootstrap. CLI options and environment variable names are unchanged.

Remaining architecture work includes the rollback-safe object-storage lifecycle.
A shared SQLAlchemy model registry is
intentional for the modular monolith, not a second persistence implementation.
