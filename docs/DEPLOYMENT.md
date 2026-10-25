# Deploying Brights (free pilot setup)

This guide puts Brights online for a **pilot / testing** using free tiers:

| Part | Service | Free tier (checked October 2026) |
|---|---|---|
| App (Django + React, one service) | Render web service, Docker | 750 hours/month; sleeps after 15 min idle, ~1 min to wake |
| Database | Neon Postgres | 1 GB, permanent, sleeps after 5 min idle |
| Tutor documents and photos | Neon storage (private bucket), or Cloudflare R2 | Neon: 5 GB · R2: 10 GB |
| Email | Brevo SMTP | 300 emails/day |

> **Before a real launch with real children's data**, read "Limits of the free setup" at the bottom
> and docs/POPIA.md. Free tiers are for proving the product works, not for running it at scale.

Why one service? Brights logs people in with a secure cookie that only works when the website and
the API share one address. In production, Django serves the built React app itself, so they do.

---

## 1. Put the code on GitHub

Render deploys from a Git repository. Keep the repo **private**: the code is your business, and a
private repo also keeps the admin path and setup details away from strangers.

First check that no secrets are committed (run in the `brights` folder):

```powershell
git status --untracked-files=all              # backend\.env must NOT appear
git check-ignore -v backend/.env               # must print a .gitignore rule
git log --all --oneline -- backend/.env        # must print nothing (never committed)
```

Then, on github.com: **New repository** → name `brights` → **Private** → leave "Add a README" and
".gitignore" unticked (the project already has them) → **Create repository**. Copy the HTTPS address it
shows (e.g. `https://github.com/<you>/brights.git`) and run:

```powershell
git branch -M main
git remote add origin https://github.com/<you>/brights.git
git push -u origin main
```

The first push opens a browser window to sign in to GitHub. After that, `git push` is enough.

## 2. Database: Neon

1. Sign up at neon.com and create a project. Choose region **AWS Europe (Frankfurt)** so it sits
   next to the Render server.
2. Create a database called `brights`.
3. Copy the **direct** connection string (not the "pooled" one). It looks like
   `postgresql://user:password@ep-xxxx.eu-central-1.aws.neon.tech/brights?sslmode=require`.
   This is your `DATABASE_URL`. Treat it like a password.

## 3. Private file storage

Render's free servers lose their disk on every deploy and restart, so documents must live elsewhere.
Brights works with any S3-compatible private bucket. Two options:

### Option A (used for the pilot): Neon storage

Same Neon project as the database, no extra sign-up and no card. It's newer (Neon calls it beta) and
its free 5 GB of monthly traffic is shared with the database, which is fine for a pilot.

1. In the Neon project: **Storage → Create bucket**, name `brights-private`, visibility **Private**.
2. **Connect → .env** shows the values. Fill these in on Render:
   - `S3_BUCKET` = `brights-private`
   - `S3_ENDPOINT_URL` = the `AWS_ENDPOINT_URL_S3` value (starts `https://br-…storage…neon.tech`)
   - `S3_REGION` = the `AWS_REGION` value (`eu-central-1`)
   - `S3_ACCESS_KEY_ID` = `AWS_ACCESS_KEY_ID` (starts `nak_live_`)
   - `S3_SECRET_ACCESS_KEY` = **Reveal credential**, then copy `AWS_SECRET_ACCESS_KEY` (starts `nsk_live_`)

### Option B: Cloudflare R2

R2 includes 10 GB free each month, but Cloudflare asks you to complete a checkout to switch R2 on,
which normally means adding a card or PayPal (you aren't charged within the free amount). If that's
not possible yet, any S3-compatible storage works with the same `S3_*` settings.

1. In the Cloudflare dashboard, open **R2** and create a bucket, e.g. `brights-private`.
   Leave **public access off** (the default). Brights never makes files public; it streams them
   through permission-checked pages.
2. Create an **R2 API token** with *Object Read & Write* permission, limited to that one bucket.
3. Note these four values:
   - `S3_BUCKET` = the bucket name
   - `S3_ENDPOINT_URL` = `https://<your-account-id>.r2.cloudflarestorage.com`
   - `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` from the token (shown once; save them in a password manager)
   - `S3_REGION` = `auto`

## 4. Email: Brevo

Render's free plan blocks the usual email ports (25, 465 and 587) since September 2025, so `render.yaml` sends through Brevo's port **2525** instead. On a paid server or another host, 587 works too.

1. Sign up at brevo.com. Add and verify the **sender** address you'll send from
   (ideally on your own domain; until then a verified personal address works for a pilot).
2. In **SMTP & API**, create an SMTP key. Note:
   - `EMAIL_HOST_USER` = your SMTP login (shown on that page)
   - `EMAIL_HOST_PASSWORD` = the SMTP key
   - `DEFAULT_FROM_EMAIL` = e.g. `Brights <hello@your-domain>` (must be the verified sender)

## 5. The app: Render

1. Sign up at render.com and connect your GitHub account.
2. **New → Blueprint**, choose your repo. Render reads `render.yaml` and creates the `brights` service
   (Docker, free plan, Frankfurt).
3. Render asks for every value marked `sync: false`. Fill them in:

| Variable | Value |
|---|---|
| `DJANGO_ADMIN_URL` | a hard-to-guess path, e.g. `staff-7f3k9q/` |
| `DATABASE_URL` | from step 2 |
| `S3_*` (incl. `S3_REGION`) | from step 3 |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | from step 4 |
| `REPORT_ALERT_EMAILS` | an inbox someone checks daily for child-safety alerts |
| `YOUTUBE_CHANNEL_URL` | optional: your channel, e.g. `https://www.youtube.com/@brights` |

`DJANGO_SECRET_KEY` is generated by Render automatically. Never reuse your development key.
The site's own address (e.g. `brights-ab12.onrender.com`) is also picked up automatically. Only when you
add your own domain do you set `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` and `FRONTEND_URL`.

4. Deploy. The first build takes a few minutes (it builds the React app, then the Python image).
   On start-up the container runs database migrations automatically.
5. Open `https://brights.onrender.com/api/health/`. You should see `{"status":"ok","database":"connected"}`.

## 6. Create your admin account

Render's free plan has no shell, so create the first admin from your laptop, pointed at the Neon
database. In `backend`, with `(venv)` active, in PowerShell:

```powershell
$env:DATABASE_URL = "postgresql://...your Neon direct URL..."
python manage.py createsuperuser
Remove-Item Env:DATABASE_URL
```

Use a long, unique password (a password manager helps). Then log in at
`https://brights.onrender.com/<your DJANGO_ADMIN_URL>`.

## 7. Check the proxy setting

Rate limits need the visitor's real IP address. While logged in to the admin, open
`https://brights.onrender.com/api/staff/request-info/`.

- `client_ip` should be **your own public IP** (compare with any "what is my IP" site).
- If it shows a different address that appears in `x_forwarded_for`, change `TRUSTED_PROXY_COUNT`
  in Render so `client_ip` matches your IP, and redeploy. Never set it higher than needed.

## 8. Smoke test

- Sign up as a parent and confirm the verification email arrives (check spam the first time).
- Use **Forgot your password?** and confirm that email too.
- Apply as a tutor, upload a document, approve it in the admin, and view the document there.
- Submit a test report and check the alert reaches `REPORT_ALERT_EMAILS`.
- Run the security check locally against production settings:
  `python manage.py check --deploy`. Two warnings are expected until you have your own domain
  (`SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD`). Turn those on only once every
  subdomain of your own domain is HTTPS-only; they are hard to undo.

## Running the pilot

- **Tutors need an approved photo** to appear in search. Approve photos (and applications) in the
  admin regularly; a tutor waiting for approval is invisible to learners.
- **How-to videos:** upload the video to YouTube (Public or Unlisted), then in the admin open
  **Guide videos → Add**, paste the YouTube link, choose the topic, and tick **Published**. It appears
  on every tutor's Home straight away. Untick Published to hide it.
- **Testers:** ask them to report anything odd, with a screenshot and the time it happened, so you
  can find it in Render's logs.

## Updating

Push to the main branch; Render rebuilds and redeploys automatically. Migrations run on start-up.
Run `python manage.py test` locally before every push.

## Backups

Neon's free plan keeps only a short history. Take your own backup regularly (weekly at least):

```powershell
pg_dump "postgresql://...your Neon URL..." --format=custom --file brights-YYYY-MM-DD.dump
```

Store backups encrypted (they contain children's personal information) and delete old ones.

## Limits of the free setup

- **Sleep:** the site sleeps after 15 minutes idle; the next visitor waits about a minute.
- **Single small server:** fine for a pilot, not for heavy traffic.
- **Traffic allowance:** since Render's August 2026 plan change, a free workspace includes 5 GB of
  outbound traffic a month. Tutor photos are sent through the app, so they count towards it. Plenty
  for a test group; watch the usage page if many people start using it.
- **Data abroad:** Render (Frankfurt), Neon (Frankfurt), Cloudflare and Brevo are outside South Africa.
  POPIA section 72 controls sending personal information abroad. See docs/POPIA.md.
- **Hours:** 750 free hours a month covers one always-on service; a second service would run out.

## Moving to a paid or South African host later

Nothing in the code is tied to Render. The same `Dockerfile` runs on any Docker host, including a South African VPS.
On a server with a permanent disk you can switch documents back to local storage
(`PRIVATE_STORAGE_BACKEND=local`) and keep them in South Africa.
