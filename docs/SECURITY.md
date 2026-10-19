# Brights security overview

What protects Brights, what an independent review found, and what is still open.
This is not a certification. Review it again before launch and after big changes.

## Main protections

**Accounts and access**
- Logins use secure, HttpOnly session cookies plus CSRF protection. Admin rights come only from
  `is_staff`, which no API can set.
- Rate limits: 10 logins/min per IP; 30 sign-ups/hour per IP; per-account lockout after 10 failed
  logins (15 minutes); admin login 10 attempts per 15 min per IP.
- Admin accounts can't log in through the public API (they can download ID documents, so they use
  the admin site only). The admin path is configurable (`DJANGO_ADMIN_URL`).
- Email verification is required before contacting tutors, reporting, or submitting a tutor
  application. Password-reset and verification links are signed, single-use and expire after 3 days;
  a password reset logs out all other sessions.

**Tutor verification data**
- Documents (ID copies, Matric results, qualifications) are stored privately (local disk or a
  private R2 bucket), with random file names. The file type is checked from the content.
- Documents can only be downloaded by staff who hold the "Can view application document"
  permission. When viewed in the browser they are sandboxed (no scripts).
- Application status changes only through `tutors/services.py`, with a permanent audit trail.
  Admins can't review their own application.

**Public profiles and contact**
- Only approved, complete, active tutors who aren't under a safety hold are public, and only
  their approved subjects. WhatsApp numbers, emails, dates of birth, marks and documents are never
  in public responses.
- Bios and availability can't contain phone numbers, emails, links or social handles, so contact
  always goes through the logged, limited WhatsApp flow.
- Photos are re-encoded (removes GPS/EXIF), size-limited and shown only after an admin has seen
  that exact photo.
- WhatsApp numbers are released only to verified learner/parent accounts: 10 new tutors per account
  per day and 60 per IP per day. Learners under 18 must confirm safety guidance first.

**Safety reports**
- Child-safety reports from a learner or parent who contacted the tutor hide that tutor
  immediately until an admin closes the report. Other child-safety reports alert admins urgently.
- Reporter identity is never sent to the tutor. Reports can't be deleted.

**Production configuration**
- `DEBUG` is off by default. HTTPS redirect, HSTS (30 days), secure cookies, nosniff, X-Frame-Options
  DENY, Referrer-Policy same-origin and Cross-Origin-Opener-Policy are set.
- The React app is served with a strict Content-Security-Policy (only its own scripts, styles,
  fonts and images). The only outside sources allowed are YouTube thumbnails (`i.ytimg.com`) and
  the privacy-enhanced YouTube player (`www.youtube-nocookie.com`, frames only) for the tutor how-to
  videos. Video links are reduced to an 11-character YouTube ID before saving, so nothing else can be embedded.
- Tutor profile views are counted per day as a number only; who viewed a profile is never stored
  (one count per visitor per day, using a hashed key in the cache).
- Request bodies over 8 MB are refused before being read.
- The Docker image runs as a non-root user and contains no secrets. Logs omit query strings, so
  tokens in email links aren't logged.
- `python manage.py check --deploy` includes a Brights check that fails if emails would be printed
  to logs instead of sent.

## Independent review (October 2026)

A separate reviewer audited the code. It found **no critical or high-severity issues**.
All medium and low findings were fixed and covered by tests:

| Finding | Fix |
|---|---|
| Fake child-safety reports could hide any tutor | Instant hide only for reports from learners/parents who contacted the tutor |
| Tutors could put their number in their bio, bypassing the safe contact flow | Contact details blocked in bio and availability |
| WhatsApp numbers could be scraped with many accounts | Per-IP contact and sign-up limits; atomic per-account limit |
| API login was a faster way to guess admin passwords | Staff blocked from API login; per-account lockout everywhere |
| One photo upload could exhaust server memory | Lower pixel limit; images shrunk before processing; upload limit |
| Large uploads read fully before being rejected | 8 MB request cap |
| A swapped photo could be approved unseen | Approval shows each photo and only approves that exact file |
| Edits could race with submission | Row locks on edit, upload and delete |
| Inline documents shown without sandbox | Sandbox CSP on document views |
| Verify-email link revealed whether an account was verified | Token checked first |
| Hidden tutors' photos cached for a day | Short private caching |
| `/index.html` served without the security policy | Same headers on all HTML files |

## Accepted risks (revisit before launch)

- **Sign-up reveals whether an email is registered** ("An account with this email already exists").
  Common practice and helpful to users; login and password reset don't reveal it.
- **Password-reset responses can be slightly slower for existing accounts** (the email is sent while
  the request waits). Low risk; could move to a background job later.
- **Any superuser can do everything.** Keep very few superusers. Give other team members `is_staff`
  plus only the permissions they need.
- **No two-factor login for admins yet.** Use long unique passwords and turn on 2FA for the hosting,
  database, R2, email and GitHub accounts.
- **Migrations run at container start.** Fine for one instance; use a separate release step if you
  ever run several.

## Operating checklist

- Keep `DJANGO_SECRET_KEY`, `DATABASE_URL`, R2 keys and the SMTP key only in Render's settings and a
  password manager. Rotate them if anyone with access leaves.
- Check `REPORT_ALERT_EMAILS` daily. Decide who responds to urgent reports, and how fast.
- Run `python manage.py test`, `pip-audit -r requirements.txt` and `npm audit` before releases.
- Back up the database regularly (see DEPLOYMENT.md).
