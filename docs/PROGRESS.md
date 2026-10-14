# Brights — Working Summary

## Current phase
Phase 1 — Environment and project structure (in progress)

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
- Admin access granted only via Django `is_staff`; never settable through the API.
- Brand colours come from the Brights logo (navy, blue, teal, gold, orange).

## Implemented
- (nothing yet)

## Open decisions
- Custom User model and role design — settle at start of Phase 3, before the first migration.

## Needs review before launch
- POPIA, especially children's personal information: consent, guardian involvement, data minimisation, retention of verification documents.

## Next steps
- Finish Phase 1, then Phase 2 (Django project + React app talking to each other).
