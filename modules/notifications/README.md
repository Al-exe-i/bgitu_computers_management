# Notifications

This module owns notification subscriptions, recipient selection, payload
rendering and delivery orchestration. Its SQLAlchemy model, repository and HTTP
schemas live here; the HTTP routes and dependency wiring remain composition code.

Other business modules use only `public.py`: immutable notification commands and
the `NotificationDelivery` protocol. Identity and inventory schedule delivery
after commit. Recipient selection reads audience context through inventory's
public directory contract, without importing its ORM models or repositories.

The delivery service uses `RealtimeNotificationPublisher`; Redis and SSE remain
shared transport infrastructure. Notification streams still require authentication;
public audience updates use a separate stream. This move does not change API
payloads, database tables, permissions or subscription rules.

Delivery is best effort, not durable: no outbox, acknowledgement or replay is
introduced. `sent` counts successful publish calls, not messages read by clients.
Publisher failures propagate to the post-commit runner for logging and cannot
undo an already committed business transaction. Repositories flush but never
commit; the request transaction owns subscription writes.

Architecture tests enforce public-only imports between business modules and keep
contracts free of infrastructure. The renderer has no database or transport
dependencies. Audit is provided through administration's public contract.
Operational CLI/bootstrap now uses module-owned provisioning services.
Rollback-safe file lifecycle handling remains separate work, outside this module.
