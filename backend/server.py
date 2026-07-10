from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import logging
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict


# ---------------- Setup ----------------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="PURNASREE API")
api_router = APIRouter(prefix="/api")

JWT_ALGORITHM = "HS256"


# ---------------- Utils ----------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)


async def get_current_admin(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=401, detail="Not authorized")
        user.pop("password_hash", None)
        user.pop("_id", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------- Models ----------------
class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    category: str
    price: float
    image_url: str = ""
    stock: int = 100
    class_level: str = ""
    subject: str = ""
    featured: bool = False
    created_at: str = Field(default_factory=now_iso)


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    category: str
    price: float
    image_url: str = ""
    stock: int = 100
    class_level: str = ""
    subject: str = ""
    featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    class_level: Optional[str] = None
    subject: Optional[str] = None
    featured: Optional[bool] = None


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int
    image_url: str = ""


class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    address: str
    notes: str = ""
    items: List[OrderItem]


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    phone: str
    address: str
    notes: str = ""
    items: List[OrderItem]
    total: float
    status: str = "pending"  # pending, confirmed, delivered, cancelled
    created_at: str = Field(default_factory=now_iso)


class OrderStatusUpdate(BaseModel):
    status: str


class LoginInput(BaseModel):
    email: str
    password: str


# ---------------- Public: Products ----------------
@api_router.get("/products", response_model=List[Product])
async def list_products(category: Optional[str] = None, featured: Optional[bool] = None):
    q = {}
    if category:
        q["category"] = category
    if featured is not None:
        q["featured"] = featured
    docs = await db.products.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [Product(**d) for d in docs]


@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    doc = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**doc)


@api_router.get("/categories")
async def list_categories():
    cats = await db.products.distinct("category")
    return {"categories": sorted([c for c in cats if c])}


@api_router.get("/store-info")
async def store_info():
    return {
        "name": os.environ.get("STORE_NAME", "PURNASREE"),
        "whatsapp": os.environ.get("STORE_WHATSAPP", ""),
    }


# ---------------- Public: Orders ----------------
@api_router.post("/orders", response_model=Order)
async def create_order(payload: OrderCreate):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    total = sum(i.price * i.quantity for i in payload.items)
    order = Order(
        customer_name=payload.customer_name.strip(),
        phone=payload.phone.strip(),
        address=payload.address.strip(),
        notes=payload.notes.strip(),
        items=payload.items,
        total=round(total, 2),
    )
    await db.orders.insert_one(order.model_dump())
    return order


# ---------------- Auth ----------------
@api_router.post("/auth/login")
async def login(payload: LoginInput, response: Response):
    email = payload.email.strip().lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], user["email"])
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "name": user.get("name", ""), "role": user["role"]},
    }


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_admin)):
    return user


# ---------------- Admin: Products ----------------
@api_router.post("/admin/products", response_model=Product)
async def create_product(payload: ProductCreate, _: dict = Depends(get_current_admin)):
    product = Product(**payload.model_dump())
    await db.products.insert_one(product.model_dump())
    return product


@api_router.put("/admin/products/{product_id}", response_model=Product)
async def update_product(product_id: str, payload: ProductUpdate, _: dict = Depends(get_current_admin)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.products.update_one({"id": product_id}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    doc = await db.products.find_one({"id": product_id}, {"_id": 0})
    return Product(**doc)


@api_router.delete("/admin/products/{product_id}")
async def delete_product(product_id: str, _: dict = Depends(get_current_admin)):
    res = await db.products.delete_one({"id": product_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}


# ---------------- Admin: Orders ----------------
@api_router.get("/admin/orders", response_model=List[Order])
async def list_orders(status: Optional[str] = None, _: dict = Depends(get_current_admin)):
    q = {}
    if status:
        q["status"] = status
    docs = await db.orders.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [Order(**d) for d in docs]


@api_router.get("/admin/orders/stats")
async def order_stats(_: dict = Depends(get_current_admin)):
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}, "total": {"$sum": "$total"}}}]
    result = await db.orders.aggregate(pipeline).to_list(100)
    stats = {"pending": 0, "confirmed": 0, "delivered": 0, "cancelled": 0, "revenue": 0.0, "orders": 0}
    for r in result:
        status = r["_id"]
        if status in stats:
            stats[status] = r["count"]
        stats["orders"] += r["count"]
        if status in ("confirmed", "delivered"):
            stats["revenue"] += r.get("total", 0)
    stats["revenue"] = round(stats["revenue"], 2)
    return stats


@api_router.put("/admin/orders/{order_id}/status", response_model=Order)
async def update_order_status(order_id: str, payload: OrderStatusUpdate, _: dict = Depends(get_current_admin)):
    if payload.status not in ("pending", "confirmed", "delivered", "cancelled"):
        raise HTTPException(status_code=400, detail="Invalid status")
    res = await db.orders.update_one({"id": order_id}, {"$set": {"status": payload.status}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    doc = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return Order(**doc)


@api_router.delete("/admin/orders/{order_id}")
async def delete_order(order_id: str, _: dict = Depends(get_current_admin)):
    res = await db.orders.delete_one({"id": order_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"ok": True}


# ---------------- Seed ----------------
SEED_PRODUCTS = [
    {"name": "NCERT Mathematics — Class 10", "category": "NCERT Books", "price": 240, "class_level": "Class 10", "subject": "Mathematics",
     "description": "Official NCERT textbook for Class 10 Mathematics. Latest edition.",
     "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80", "featured": True},
    {"name": "NCERT Science — Class 9", "category": "NCERT Books", "price": 220, "class_level": "Class 9", "subject": "Science",
     "description": "Official NCERT Class 9 Science textbook covering Physics, Chemistry and Biology.",
     "image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&q=80", "featured": True},
    {"name": "NCERT English — Beehive Class 9", "category": "NCERT Books", "price": 180, "class_level": "Class 9", "subject": "English",
     "description": "NCERT English literature reader for Class 9.",
     "image_url": "https://images.unsplash.com/photo-1519682337058-a94d519337bc?w=800&q=80"},
    {"name": "NCERT Social Science — Class 8", "category": "NCERT Books", "price": 200, "class_level": "Class 8", "subject": "Social Science",
     "description": "History, Geography and Civics combined NCERT textbook.",
     "image_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?w=800&q=80"},
    {"name": "NCERT Hindi Kshitij — Class 10", "category": "NCERT Books", "price": 170, "class_level": "Class 10", "subject": "Hindi",
     "description": "Hindi core textbook Kshitij for Class 10 students.",
     "image_url": "https://images.unsplash.com/photo-1531988042231-d39a9cc12a9a?w=800&q=80"},
    {"name": "Classmate Notebook 200 Pages", "category": "Notebooks", "price": 90,
     "description": "Single line ruled notebook, 200 pages, hard bound.",
     "image_url": "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=800&q=80", "featured": True},
    {"name": "Long Notebook — Four Line 172 Pages", "category": "Notebooks", "price": 75,
     "description": "Perfect for younger classes practicing handwriting.",
     "image_url": "https://images.unsplash.com/photo-1517842645767-c639042777db?w=800&q=80"},
    {"name": "Practical Copy — 100 Pages", "category": "Notebooks", "price": 65,
     "description": "One side ruled, one side plain — ideal for lab records.",
     "image_url": "https://images.unsplash.com/photo-1494200483035-a2da43d2135e?w=800&q=80"},
    {"name": "Reynolds 045 Ball Pen (Pack of 10)", "category": "Pens & Pencils", "price": 100,
     "description": "Smooth writing ball pens. Blue ink. Pack of 10.",
     "image_url": "https://images.unsplash.com/photo-1585336261022-680e295ce3fe?w=800&q=80", "featured": True},
    {"name": "Apsara Platinum Pencils (Pack of 10)", "category": "Pens & Pencils", "price": 80,
     "description": "Extra dark, extra smooth pencils. HB grade.",
     "image_url": "https://images.unsplash.com/photo-1568871391265-e2cbed3ec9f4?w=800&q=80"},
    {"name": "Nataraj Geometry Box", "category": "Pens & Pencils", "price": 150,
     "description": "Complete geometry set with compass, protractor, scale and set squares.",
     "image_url": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&q=80"},
    {"name": "Faber-Castell Watercolour Set", "category": "Art Supplies", "price": 220,
     "description": "24 shade water colour cake set with brush.",
     "image_url": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=800&q=80"},
    {"name": "Camlin Oil Pastels — 25 Shades", "category": "Art Supplies", "price": 145,
     "description": "Vibrant, smooth oil pastels for young artists.",
     "image_url": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=800&q=80", "featured": True},
    {"name": "A4 Drawing Sheet (Pack of 25)", "category": "Art Supplies", "price": 90,
     "description": "Thick 150 GSM white cartridge sheets.",
     "image_url": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800&q=80"},
    {"name": "Skybags School Backpack", "category": "School Supplies", "price": 899,
     "description": "Durable 30L school backpack with padded straps.",
     "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80"},
    {"name": "Stainless Steel Water Bottle 750ml", "category": "School Supplies", "price": 320,
     "description": "Leak-proof insulated bottle for school.",
     "image_url": "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=800&q=80"},
    {"name": "Stapler with Pins Set", "category": "Office Supplies", "price": 145,
     "description": "Compact metal stapler with 1000 pins included.",
     "image_url": "https://images.unsplash.com/photo-1568667256549-094345857637?w=800&q=80"},
    {"name": "Sticky Notes — 5 Colour Pad", "category": "Office Supplies", "price": 85,
     "description": "500 sheets of sticky notes in 5 pastel shades.",
     "image_url": "https://images.unsplash.com/photo-1512314889357-e157c22f938d?w=800&q=80"},
]


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "owner@purnasree.in").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "purnasree@2026")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        user_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": user_id,
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Purnasree Owner",
            "role": "admin",
            "created_at": now_iso(),
        })
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )


async def seed_products():
    count = await db.products.count_documents({})
    if count > 0:
        return
    for p in SEED_PRODUCTS:
        product = Product(**p)
        await db.products.insert_one(product.model_dump())


@app.on_event("startup")
async def on_startup():
    await db.users.create_index("email", unique=True)
    await db.products.create_index("category")
    await db.orders.create_index("created_at")
    await seed_admin()
    await seed_products()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


