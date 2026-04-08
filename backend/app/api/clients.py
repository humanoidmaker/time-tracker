from fastapi import APIRouter, Depends
from bson import ObjectId
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/clients", tags=["clients"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_clients(db=Depends(get_db), user=Depends(get_current_user)):
    return {"success": True, "clients": [s(d) for d in await db.clients.find().sort("name", 1).to_list(100)]}

@router.post("/")
async def create(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data["slug"] = data["name"].lower().replace(" ", "-")
    r = await db.clients.insert_one(data)
    return {"success": True, "id": str(r.inserted_id)}

@router.get("/{cid}")
async def get_client(cid: str, db=Depends(get_db), user=Depends(get_current_user)):
    doc = await db.clients.find_one({"_id": ObjectId(cid)})
    if not doc: return {"success": False}
    projects = await db.projects.find({"client_id": str(doc["_id"])}).to_list(50)
    return {"success": True, "client": s(doc), "projects": [s(p) for p in projects]}

@router.put("/{cid}")
async def update(cid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data.pop("id", None); data.pop("_id", None)
    await db.clients.update_one({"_id": ObjectId(cid)}, {"$set": data})
    return {"success": True}
