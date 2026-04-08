from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import get_db
from app.utils.auth import get_current_user
import random, string

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("/generate")
async def generate(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    client = await db.clients.find_one({"_id": ObjectId(data["client_id"])})
    project = await db.projects.find_one({"_id": ObjectId(data["project_id"])})
    if not client or not project: raise HTTPException(404, "Client or project not found")

    entries = await db.time_entries.find({"project_id": data["project_id"], "status": "completed", "date": {"$gte": data.get("from_date", "2000-01-01"), "$lte": data.get("to_date", "2099-12-31")}}).to_list(1000)

    total_minutes = sum(e.get("duration_minutes", 0) for e in entries)
    total_hours = round(total_minutes / 60, 2)
    rate = project.get("hourly_rate", 500)
    subtotal = round(total_hours * rate, 2)
    gst = round(subtotal * 0.18, 2)

    now = datetime.now(timezone.utc)
    invoice = {
        "invoice_number": f"INV-{now.strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=4))}",
        "client_id": data["client_id"], "client_name": client["name"],
        "project_id": data["project_id"], "project_name": project["name"],
        "from_date": data.get("from_date", ""), "to_date": data.get("to_date", ""),
        "entries_count": len(entries), "total_hours": total_hours,
        "hourly_rate": rate, "subtotal": subtotal, "gst": gst,
        "total": round(subtotal + gst, 2),
        "status": "draft", "created_at": now,
    }
    r = await db.invoices.insert_one(invoice)
    invoice["id"] = str(r.inserted_id); del invoice["_id"]
    return {"success": True, "invoice": invoice}

@router.get("/")
async def list_invoices(db=Depends(get_db), user=Depends(get_current_user)):
    return {"success": True, "invoices": [s(d) for d in await db.invoices.find().sort("created_at", -1).to_list(100)]}

@router.get("/{iid}")
async def get_invoice(iid: str, db=Depends(get_db)):
    doc = await db.invoices.find_one({"_id": ObjectId(iid)})
    if not doc: raise HTTPException(404, "Not found")
    return {"success": True, "invoice": s(doc)}

@router.put("/{iid}/status")
async def update_status(iid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    await db.invoices.update_one({"_id": ObjectId(iid)}, {"$set": {"status": data["status"]}})
    return {"success": True}
