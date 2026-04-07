# TimeLog - Project Time Tracker

Project time tracker with start/stop timer, project/task management, weekly timesheets, client management, and invoice generation.

## Tech Stack
- Backend: Python FastAPI + Motor (async MongoDB)
- Frontend: React 18 + Vite + TypeScript + Tailwind CSS
- Database: MongoDB

## Setup
```bash
docker-compose up
# Or:
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## Seed Data
```bash
cd backend && python -m scripts.seed_admin && python -m scripts.seed_sample_data
```

## Login
- Admin: admin@time.local / admin123
