# Database Infrastructure

`app/db` is infrastructure-only in the restructured server architecture.

It owns:

- MongoDB connection setup
- Redis connection setup
- collection accessors
- database indexes and validators
- database integration notes

It does not own:

- HTTP routes
- domain services
- CRUD facades
- user-facing request/response schemas

Domain runtime code now lives under `app/auth`, `app/users`, `app/quiz`, `app/share`, `app/notifications`, and `app/email_platform`.
