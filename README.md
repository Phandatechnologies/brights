# Brights

A tutoring marketplace by Phanda Technologies, connecting South African high school learners (Grades 8–12) and their parents with verified tutors.

## Structure

- `backend/` — Django + Django REST Framework API (PostgreSQL)
- `frontend/` — React + TypeScript + Tailwind (added in Phase 2)
- `docs/PROGRESS.md` — working summary of phases, decisions and open issues

## Backend setup (Windows / PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then edit .env with real values
```

Secrets live only in `backend/.env`, which is git-ignored.
