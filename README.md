# Brights

A tutoring marketplace by Phanda Technologies, connecting South African high school learners (Grades 8–12) and their parents with verified tutors.

## Structure

- `backend/` — Django + Django REST Framework API (PostgreSQL)
- `frontend/` — React + TypeScript + Tailwind (Vite)
- `docs/PROGRESS.md` — working summary of phases, decisions and open issues
- `docs/DEPLOYMENT.md` — putting Brights online (free pilot: Render + Neon + Cloudflare R2 + Brevo)
- `docs/SECURITY.md` — how Brights is protected, review findings, accepted risks
- `docs/POPIA.md` — privacy-law checklist (needs legal input before launch)
- `Dockerfile`, `render.yaml` — production image and Render blueprint

## Backend setup (Windows / PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then edit .env with real values
```

Secrets live only in `backend/.env`, which is git-ignored.

### Run the backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py test        # run automated tests
python manage.py runserver   # http://127.0.0.1:8000/api/health/
```

## Frontend setup

```powershell
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

In development, Vite forwards `/api/*` requests to Django on port 8000, so run both servers at the same time.

### Try it on your phone

With your phone on the same Wi-Fi (or with the laptop on your phone's hotspot), run this from the `brights` folder:

```powershell
.\phone-dev.ps1
```

It finds the laptop's current network address, opens both servers with that address allowed, and prints the link to open on your phone. Close the two server windows to stop.

## Before every release

```powershell
cd backend
python manage.py test
cd ../frontend
npm run lint
npm run build
```
