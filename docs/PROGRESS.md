# Brights — Working Summary

## Current phase
Phase 2 — Basic backend and frontend apps (built; awaiting verification on laptop)

## Environment (developer laptop, Windows / PowerShell)
- Python 3.13.0, pip 26.2.1
- Node 24.19.0, npm 12.2.0
- Git 2.55.0
- PostgreSQL 18.6
- PowerShell execution policy (CurrentUser): RemoteSigned

## Decisions
- Build on the developer laptop; one repo with `backend/` and `frontend/`.
- Stack: React + TypeScript + Tailwind (Vite) / Django + DRF / PostgreSQL.
- Django apps by domain: `accounts`, `tutors`, `moderation`.
- No Docker until deployment requires it.
- DRF default permission is `IsAuthenticated`; public endpoints must opt out explicitly.
- No CORS library in development: Vite proxies `/api` to Django.
- Do NOT run `migrate` until the custom User model exists (Phase 3).
- `brights_user` has CREATEDB so Django can create a temporary test database.
- Admin access granted only via Django `is_staff`; never settable through the API.
- Brand colours come from the Brights logo (navy, blue, teal, gold, orange).

## Implemented
- Phase 1 (complete): repo initialised, .gitignore verified (`.env` and `venv/` ignored), backend venv with Django, DRF, psycopg, python-dotenv; PostgreSQL database `brights` owned by `brights_user`; `.env` created locally.
- Phase 2: Django project `config` (settings read from `.env`, PostgreSQL, DRF secure-by-default `IsAuthenticated`); `core` app with public `GET /api/health/` + 3 tests; React + TS + Tailwind v4 frontend (Vite) with brand theme and a status page calling the API through the Vite dev proxy.

## Open decisions
- Custom User model and role design — settle at start of Phase 3, before the first migration.

## Needs review before launch
- POPIA, especially children's personal information: consent, guardian involvement, data minimisation, retention of verification documents.

## Next steps
- Verify Phase 2 on laptop, commit.
- Phase 3: custom User model + roles, authentication.
