import asyncio, sys, random
from datetime import datetime, timezone, timedelta
sys.path.insert(0, ".")
from app.core.database import init_db, get_db

CLIENTS = [("Apex Solutions", "Tech consulting"), ("GreenLeaf Corp", "Organic products"), ("Skyline Media", "Digital agency"), ("NextGen Labs", "R&D firm"), ("CloudBridge Inc", "Cloud services")]
PROJECTS = [
    ("Website Redesign", 0, 800, 40, "active"), ("Mobile App Development", 0, 1200, 80, "active"),
    ("API Integration", 1, 600, 30, "active"), ("Dashboard Analytics", 1, 900, 50, "active"),
    ("Brand Identity", 2, 500, 25, "completed"), ("Social Media Campaign", 2, 400, 20, "active"),
    ("Data Pipeline", 3, 1000, 60, "active"), ("Cloud Migration", 4, 1500, 100, "active"),
]
TASKS = ["Frontend development", "Backend API", "Database design", "Code review", "Bug fixing", "Testing", "Documentation", "Client meeting", "Design mockups", "Deployment", "Research", "Planning"]

async def seed():
    await init_db()
    db = await get_db()
    if await db.projects.count_documents({}) > 0:
        print("Data exists"); return

    admin = await db.users.find_one({"role": "admin"})
    uid = str(admin["_id"]) if admin else "system"

    client_ids = []
    for name, desc in CLIENTS:
        r = await db.clients.insert_one({"name": name, "slug": name.lower().replace(" ", "-"), "company": name, "email": f"contact@{name.split()[0].lower()}.example.com", "phone": f"987655{len(client_ids):04d}", "address": "Business District", "gstin": ""})
        client_ids.append(str(r.inserted_id))

    project_ids = []
    for name, ci, rate, budget, status in PROJECTS:
        r = await db.projects.insert_one({"name": name, "slug": name.lower().replace(" ", "-"), "client_id": client_ids[ci], "description": f"{name} project", "hourly_rate": rate, "budget_hours": budget, "status": status, "color": random.choice(["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899"])})
        project_ids.append(str(r.inserted_id))

    now = datetime.now(timezone.utc)
    for i in range(50):
        day = random.randint(0, 13)
        date = (now - timedelta(days=day)).strftime("%Y-%m-%d")
        pid = random.choice(project_ids)
        start_hour = random.randint(9, 16)
        duration = random.randint(30, 240)
        start_time = (now - timedelta(days=day)).replace(hour=start_hour, minute=0, second=0)
        end_time = start_time + timedelta(minutes=duration)
        await db.time_entries.insert_one({
            "user_id": uid, "project_id": pid,
            "task_description": random.choice(TASKS),
            "start_time": start_time.isoformat(), "end_time": end_time.isoformat(),
            "duration_minutes": duration, "status": "completed", "date": date,
        })

    # 3 invoices
    for i, status in enumerate(["paid", "sent", "draft"]):
        ci = client_ids[i % len(client_ids)]
        pi = project_ids[i % len(project_ids)]
        proj = await db.projects.find_one({"_id": __import__("bson").ObjectId(pi)})
        rate = proj.get("hourly_rate", 500)
        hours = random.randint(20, 60)
        subtotal = hours * rate
        gst = round(subtotal * 0.18, 2)
        await db.invoices.insert_one({
            "invoice_number": f"INV-{now.strftime('%Y%m%d')}-{3000+i}",
            "client_id": ci, "client_name": CLIENTS[i % len(CLIENTS)][0],
            "project_id": pi, "project_name": proj["name"],
            "total_hours": hours, "hourly_rate": rate,
            "subtotal": subtotal, "gst": gst, "total": round(subtotal + gst, 2),
            "status": status, "created_at": now - timedelta(days=i * 7),
        })

    print(f"Seeded: {len(CLIENTS)} clients, {len(PROJECTS)} projects, 50 time entries, 3 invoices")

asyncio.run(seed())
