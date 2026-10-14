# Brights — Working Summary

## Current phase
Phase 3b — Frontend sign-up, login and protected routes (next)

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
- Login = email + password; one account type per user, fixed at sign-up; admins = `is_staff` only.
- Auth = Django session cookies (HttpOnly) + CSRF. Deployment must keep frontend and API on the same site (e.g. brights.co.za / api.brights.co.za).
- Sign-up rules: tutors 18+; parents 18+; learners 12+; learners under 18 tick guardian consent + give guardian name (founder's choice: checkbox only).
- Guardian details discarded for anyone who isn't a minor learner (data minimisation).
- `brights_user` has CREATEDB so Django can create a temporary test database.
- Admin access granted only via Django `is_staff`; never settable through the API.
- Brand colours come from the Brights logo (navy, blue, teal, gold, orange).

## Implemented
- Phase 1 (complete): repo initialised, .gitignore verified (`.env` and `venv/` ignored), backend venv with Django, DRF, psycopg, python-dotenv; PostgreSQL database `brights` owned by `brights_user`; `.env` created locally.
- Phase 2: Django project `config` (settings read from `.env`, PostgreSQL, DRF secure-by-default `IsAuthenticated`); `core` app with public `GET /api/health/` + 3 tests; React + TS + Tailwind v4 frontend (Vite) with brand theme and a status page calling the API through the Vite dev proxy. Verified on laptop: tests pass, status page shows API OK / Database Connected.
- Phase 3a: `accounts` app — custom `User` (email login, lowercase-normalised; first/last name; date_of_birth; account_type learner/parent/tutor; guardian_name + guardian_consent_given_at for minor learners; computed `is_minor`). Sign-up rules in `accounts/rules.py`. Session auth endpoints: `/api/auth/csrf|register|login|logout|me/`. CSRF enforced on anonymous register/login; auth endpoints rate-limited 10/min. Admin configured. 30 new tests (33 total).

## Open decisions

## Needs review before launch
- POPIA, especially children's personal information: consent, guardian involvement, data minimisation, retention of verification documents.
- Guardian consent is a self-declared checkbox — weak evidence; consider guardian email confirmation before launch.
- Email verification deferred to Phase 9.

## Next steps
- Phase 3b: React Router, auth context, sign-up (consent fields shown only for under-18 learners), login, protected routes.
