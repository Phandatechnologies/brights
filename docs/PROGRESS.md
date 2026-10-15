# Brights — Working Summary

## Current phase
Phase 9 — Testing, security review and deployment preparation (next)

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
- Tutor decisions (Phase 4): grades chosen per subject; tutor types Matric marks, admin verifies against the document; required uploads — academic: ID + Matric certificate/statement of results; teacher: ID + teaching qualification + SACE certificate (+ SACE number and qualification name); drafts allowed.
- Moderation decisions (Phase 8): child-safety reports hide the tutor until reviewed; logged-in reporters only; admins emailed on urgent reports; reporters emailed on receipt and closure.
- Contact decisions (Phase 7): under-18 learners allowed to contact tutors after a one-time safety step.
- Profile/search decisions (Phase 6): anyone can browse, contact needs login; areas from an admin-managed list; optional photo with admin approval; full names shown publicly; one hourly rate; exact Matric marks NOT shown publicly (verification label only).
- Review decisions (Phase 5): per-subject approval; review in customised Django admin; email + dashboard notifications; rejected tutors may reapply after 30 days.
- Guardian details discarded for anyone who isn't a minor learner (data minimisation).
- `brights_user` has CREATEDB so Django can create a temporary test database.
- Admin access granted only via Django `is_staff`; never settable through the API.
- Brand colours come from the Brights logo (navy, blue, teal, gold, orange).

## Implemented
- Phase 1 (complete): repo initialised, .gitignore verified (`.env` and `venv/` ignored), backend venv with Django, DRF, psycopg, python-dotenv; PostgreSQL database `brights` owned by `brights_user`; `.env` created locally.
- Phase 2: Django project `config` (settings read from `.env`, PostgreSQL, DRF secure-by-default `IsAuthenticated`); `core` app with public `GET /api/health/` + 3 tests; React + TS + Tailwind v4 frontend (Vite) with brand theme and a status page calling the API through the Vite dev proxy. Verified on laptop: tests pass, status page shows API OK / Database Connected.
- Phase 3a: `accounts` app — custom `User` (email login, lowercase-normalised; first/last name; date_of_birth; account_type learner/parent/tutor; guardian_name + guardian_consent_given_at for minor learners; computed `is_minor`). Sign-up rules in `accounts/rules.py`. Session auth endpoints: `/api/auth/csrf|register|login|logout|me/`. CSRF enforced on anonymous register/login; auth endpoints rate-limited 10/min. Admin configured. 30 new tests (33 total).
- Phase 3b: React Router; `AuthProvider` (session check on load, login/register/logout); `RequireAuth` and `GuestOnly` route guards; pages: Home, Login, Register (guardian consent section appears only for 12–17-year-old learners; live age warnings), Dashboard, Status (/status), 404. API client sends CSRF header and maps Django errors to form fields. Browser-tested end to end (11 flows).
- Phase 8: `moderation` app. `Report` (reporter, tutor, category, description 20–2000 chars, optional incident date, urgent flag, status open/closed, outcome dismissed/warned/suspended, internal notes; never deletable). Logged-in users report from the tutor profile or their contacted list (`/tutors/:id/report`); limits: 5/day, one open report per tutor. Child-safety reports hide the tutor from search and contact immediately (derived in `profiles/queries.py` from open urgent reports, so closing the report restores visibility automatically). Emails: reporter received/closed (with SAPS 10111 / Childline 116), admins on urgent (`REPORT_ALERT_EMAILS` or all superusers), tutor only if warned. Admin report queue (open + urgent first) and review page with reporter, contact history, other reports, dismiss/warn/suspend (suspend goes through the Phase 5 workflow and audit trail). 23 new tests (175 total); browser-tested end to end.
- Phase 7: `contact` app. `POST /api/tutors/<id>/contact/` (learners and parents only; tutor must be discoverable) returns a wa.me link with a pre-filled, editable message and logs a `ContactEvent` (who, tutor, subject, grade, whether requester was a minor). Limit: 10 new tutors per account per 24 h (re-contacting allowed). Under-18 learners must confirm safety guidance once (`SafetyAcknowledgement`, versioned) before any number is released; their message identifies them as a learner. Contact history on learner/parent dashboard. Contact log read-only in admin. Frontend: subject/grade picker, safety dialog (native <dialog>), 'Open WhatsApp chat' link. 17 new tests (152 total); browser-tested minor, parent and tutor flows.
- Phase 6: `profiles` app. `Area` (admin-managed; 41 Gauteng areas seeded; 9 provinces). `TutorProfile` (bio, hourly rate R50–R2,000, online/in-person, area, availability, private WhatsApp number normalised to +27…, optional photo). Discoverability in `profiles/queries.py`: active account + approved application + ≥1 approved subject + complete profile; only approved subjects shown. Public search `/api/tutors/` with subject, grade, mode, province, area, price filters and sort; online tutors match any location unless 'in person' is chosen. Public profile `/api/tutors/<id>/` never includes WhatsApp, email, DOB, marks or documents. Photos: Pillow re-encodes to JPEG (strips EXIF/GPS, max 800px), stored privately, pending until an admin approves (admin actions), re-approval on replace. Frontend: `/tutors` search (URL-synced filters, pagination, filters collapsed on phones), `/tutors/:id` profile, `/tutor/profile` editor with listing checklist and photo upload; 'Find a tutor' in header and hero. 34 new tests (135 total); browser-tested.
- Phase 5: review workflow in `tutors/services.py` (single place that changes status; row-locked; allowed transitions only: pending→approved/more_info/rejected, approved→suspended, suspended→approved, rejected→draft after 30 days by tutor). Per-subject decisions (approved/declined + reason; at least one approved; never below 60% for academic). Admins can't review their own application. `ApplicationEvent` audit log (read-only in admin; applications with history can't be deleted). Customised Django admin review page (applicant, documents viewable inline, subject decisions, message, actions, history); application change form fully read-only. Tutor emails on every decision (console backend in dev; no sensitive details). Tutor UI shows subject decisions, reviewer notes, and reapply date/button. 25 new tests (101 total); browser-tested admin + tutor flow.
- Phase 4b: `/tutor/apply` — choose pathway, then 4 steps (application type incl. SACE/qualification for teachers; subjects with Matric mark + per-subject grade chips and live 60% warning; document upload slots per required kind with type/size checks and server reasons shown; review checklist + submit). Status page for pending/approved/rejected/suspended with reviewer note; 'more info' banner reopens editing. Tutor dashboard card shows application state. Learners/parents blocked. Browser-tested end to end (11 flows).
- Landing page redesign: full-bleed hero photo (Vitaly Gariev, Unsplash License, self-hosted as WebP in `public/images/`, credited in footer), gold star motif from the logo with one load animation (respects reduced motion), sample Matric results slip explaining the 60% rule, 4-step learner journey, safety section, tutor invite. Fonts self-hosted via Fontsource: Bricolage Grotesque (headings) + Instrument Sans (body). `/register?as=tutor` pre-selects the account type.
- Phase 4a: `tutors` app. `Subject` catalogue (47 NSC subjects seeded; admin-managed). `TutorApplication` (one per tutor; pathway academic/teacher; statuses draft → pending → more_info/approved/rejected/suspended; editable only in draft/more_info). `ApplicationSubject` (subject, Matric mark, grades per subject). `ApplicationDocument` stored in private storage (`PRIVATE_MEDIA_ROOT`, never URL-served, random filenames); PDF/JPG/PNG only, detected by file signature; 5 MB max; 10 per application. API: `/api/subjects/`, `/api/tutor/application/` (GET/POST/PATCH), `/submit/`, `/documents/` (POST, DELETE own), staff-only `/api/staff/documents/<id>/download/`. Basic Django admin with download links. 43 new tests (76 total).
- Added: show/hide password toggle (`PasswordField`) on login and sign-up.
- Fixed: CSRF origin check rejected POSTs from the Vite dev server → new `DJANGO_CSRF_TRUSTED_ORIGINS` env setting.

## Open decisions
- Show exact Matric marks on public profiles? Currently hidden (privacy default).
- Matric completion and marks are one upload (an NSC certificate/statement shows both) — confirm this satisfies the brief's 'evidence of completion' + 'evidence of marks'.
- Grade 8–9-only subjects (Natural Sciences, Social Sciences, EMS, Technology, Creative Arts) not in the subject list yet: decide how academic tutors qualify for them.
- Production document storage (private cloud bucket, ideally in SA region) — decide in Phase 9.
- Frontend has no automated tests yet (backend rules are the authority and fully tested); consider Vitest when UI logic grows.

## Needs review before launch
- Set REPORT_ALERT_EMAILS to a monitored safety inbox; define a response-time target for urgent reports and who is on call.
- Decide when and how Brights escalates reports to SAPS / child-protection services; get legal input.
- Have the minor safety guidance wording reviewed (child-protection perspective) and decide whether parents should be notified when their child contacts a tutor.
- Contact log retention period (POPIA).
- Choose an email provider and set EMAIL_* env vars (currently prints to terminal).
- Applications with an audit history can't be deleted (on_delete=PROTECT): design a POPIA-compliant account-deletion/anonymisation process that keeps the decision log.
- ID documents are special personal information: define retention period and deletion process for verification documents (POPIA).
- Landing page copy describes features not built yet (search, WhatsApp contact, reporting) — fine pre-launch, but re-check wording before going live.
- POPIA, especially children's personal information: consent, guardian involvement, data minimisation, retention of verification documents.
- Guardian consent is a self-declared checkbox — weak evidence; consider guardian email confirmation before launch.
- Email verification deferred to Phase 9.

## Next steps
- Phase 9: full security review (settings for production, HTTPS, headers, dependency audit), POPIA checklist, deployment plan.
