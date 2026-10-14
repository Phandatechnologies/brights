# Brights

A tutoring marketplace by Phanda Technologies, connecting South African high school learners (Grades 8–12) and their parents with verified tutors.

## Structure

- `backend/` — Django + Django REST Framework API (PostgreSQL)
- `frontend/` — React + TypeScript + Tailwind (Vite)
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
