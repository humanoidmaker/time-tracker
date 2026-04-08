from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_projects(client_id: str = "", status: str = "", db=Depends(get_db), user=Depends(get_current_user)):
    f = {}
    if client_id: f["client_id"] = client_id
    if status: f["status"] = status
    return {"success": True, "projects": [s(d) for d in await db.projects.find(f).sort("name", 1).to_list(100)]}

@router.get("/{pid}")
async def get_project(pid: str, db=Depends(get_db), user=Depends(get_current_user)):
    doc = await db.projects.find_one({"_id": ObjectId(pid)})
    if not doc: raise HTTPException(404, "Not found")
    # Get time summary
    pipe = [{"$match": {"project_id": pid, "status": "completed"}}, {"$group": {"_id": None, "total_minutes": {"$sum": "$duration_minutes"}, "count": {"$sum": 1}}}]
    r = await db.time_entries.aggregate(pipe).to_list(1)
    summary = r[0] if r else {"total_minutes": 0, "count": 0}
    return {"success": True, "project": s(doc), "total_hours": round(summary["total_minutes"] / 60, 1), "total_entries": summary["count"]}

@router.post("/")
async def create(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data["slug"] = data["name"].lower().replace(" ", "-")
    data.setdefault("status", "active")
    r = await db.projects.insert_one(data)
    return {"success": True, "id": str(r.inserted_id)}

@router.put("/{pid}")
async def update(pid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data.pop("id", None); data.pop("_id", None)
    await db.projects.update_one({"_id": ObjectId(pid)}, {"$set": data})
    return {"success": True}

@router.delete("/{pid}")
async def delete(pid: str, user=Depends(get_current_user), db=Depends(get_db)):
    await db.projects.delete_one({"_id": ObjectId(pid)})
    return {"success": True}
