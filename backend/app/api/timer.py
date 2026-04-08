from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/timer", tags=["timer"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("/start")
async def start(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    # Check if there is already a running timer
    running = await db.time_entries.find_one({"user_id": user["id"], "status": "running"})
    if running: raise HTTPException(400, "Timer already running. Stop it first.")
    entry = {
        "user_id": user["id"], "project_id": data["project_id"],
        "task_description": data.get("task_description", ""),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None, "duration_minutes": 0, "status": "running",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    r = await db.time_entries.insert_one(entry)
    return {"success": True, "id": str(r.inserted_id)}

@router.post("/stop/{entry_id}")
async def stop(entry_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    entry = await db.time_entries.find_one({"_id": ObjectId(entry_id), "user_id": user["id"]})
    if not entry or entry["status"] != "running": raise HTTPException(400, "No running timer found")
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(entry["start_time"])
    duration = max(1, int((now - start).total_seconds() / 60))
    await db.time_entries.update_one({"_id": ObjectId(entry_id)}, {"$set": {"end_time": now.isoformat(), "duration_minutes": duration, "status": "completed"}})
    return {"success": True, "duration_minutes": duration}

@router.get("/running")
async def running(user=Depends(get_current_user), db=Depends(get_db)):
    entry = await db.time_entries.find_one({"user_id": user["id"], "status": "running"})
    return {"success": True, "entry": s(entry) if entry else None}

@router.post("/manual")
async def manual(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    start = datetime.fromisoformat(data["start_time"])
    end = datetime.fromisoformat(data["end_time"])
    duration = max(1, int((end - start).total_seconds() / 60))
    entry = {
        "user_id": user["id"], "project_id": data["project_id"],
        "task_description": data.get("task_description", ""),
        "start_time": data["start_time"], "end_time": data["end_time"],
        "duration_minutes": duration, "status": "completed",
        "date": data.get("date", start.strftime("%Y-%m-%d")),
    }
    r = await db.time_entries.insert_one(entry)
    return {"success": True, "id": str(r.inserted_id)}

@router.get("/today")
async def today(user=Depends(get_current_user), db=Depends(get_db)):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = await db.time_entries.find({"user_id": user["id"], "date": today_str}).sort("start_time", -1).to_list(50)
    return {"success": True, "entries": [s(e) for e in entries]}

@router.get("/entries")
async def entries(project_id: str = "", db=Depends(get_db), user=Depends(get_current_user)):
    f = {"user_id": user["id"]}
    if project_id: f["project_id"] = project_id
    return {"success": True, "entries": [s(e) for e in await db.time_entries.find(f).sort("date", -1).to_list(500)]}
