from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api import auth, projects, timer, clients, invoices, settings as settings_api

@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield

app = FastAPI(title="TimeLog Time Tracker API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(timer.router)
app.include_router(clients.router)
app.include_router(invoices.router)
app.include_router(settings_api.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "TimeLog"}

@app.get("/api/stats")
async def stats():
    from app.core.database import get_db as gdb
    from datetime import datetime, timezone
    db = await gdb()
    tp = await db.projects.count_documents({"status": "active"})
    tc = await db.clients.count_documents({})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pipe = [{"$match": {"date": today, "status": "completed"}}, {"$group": {"_id": None, "hours": {"$sum": "$duration_minutes"}}}]
    r = await db.time_entries.aggregate(pipe).to_list(1)
    today_hours = round((r[0]["hours"] if r else 0) / 60, 1)
    return {"stats": {"active_projects": tp, "total_clients": tc, "today_hours": today_hours}}
