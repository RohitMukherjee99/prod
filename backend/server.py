from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import razorpay
import hmac
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Razorpay client
razorpay_key_id = os.environ.get('RAZORPAY_KEY_ID', '')
razorpay_key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
razorpay_client = None
if razorpay_key_id and razorpay_key_secret:
    razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))

# Create the main app
app = FastAPI(title="3RD OSI CONFERENCE KOLKATA 2026 API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class RegistrationCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    category: str  # delegate, student, accompanying_person, etc.
    organization: Optional[str] = None
    designation: Optional[str] = None
    address: Optional[str] = None
    accommodation_required: bool = False
    room_type: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None

class Registration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: str
    phone: str
    category: str
    organization: Optional[str] = None
    designation: Optional[str] = None
    address: Optional[str] = None
    accommodation_required: bool = False
    room_type: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    amount: int = 0
    payment_status: str = "pending"
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str

class OrderCreate(BaseModel):
    amount: int  # Amount in paise
    currency: str = "INR"
    registration_id: str

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    registration_id: str

# Pricing Configuration (amounts in INR)
PRICING = {
    "delegate_early_bird": 12000,
    "delegate_regular": 15000,
    "delegate_late": 18000,
    "student_early_bird": 6000,
    "student_regular": 8000,
    "student_late": 10000,
    "accompanying_person": 5000,
    "workshop_only": 3000,
}

ROOM_PRICING = {
    "standard": 6000,
    "deluxe": 8000,
    "suite": 12000,
}

# API Routes

@api_router.get("/")
async def root():
    return {"message": "Welcome to 3RD OSI CONFERENCE KOLKATA 2026 API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/pricing")
async def get_pricing():
    return {
        "registration": PRICING,
        "accommodation": ROOM_PRICING,
        "razorpay_key_id": razorpay_key_id
    }

@api_router.post("/registration", response_model=Registration)
async def create_registration(input_data: RegistrationCreate):
    # Calculate amount
    amount = PRICING.get(input_data.category, 0)
    
    # Add accommodation cost if required
    if input_data.accommodation_required and input_data.room_type:
        room_cost = ROOM_PRICING.get(input_data.room_type, 0)
        # Calculate nights (simplified - 2 nights default)
        nights = 2
        amount += room_cost * nights
    
    registration = Registration(
        **input_data.model_dump(),
        amount=amount * 100  # Convert to paise for Razorpay
    )
    
    doc = registration.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.registrations.insert_one(doc)
    return registration

@api_router.get("/registration/{registration_id}", response_model=Registration)
async def get_registration(registration_id: str):
    doc = await db.registrations.find_one({"id": registration_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    if isinstance(doc.get('created_at'), str):
        doc['created_at'] = datetime.fromisoformat(doc['created_at'])
    
    return Registration(**doc)

@api_router.post("/create-order")
async def create_order(order_data: OrderCreate):
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    try:
        order = razorpay_client.order.create({
            "amount": order_data.amount,
            "currency": order_data.currency,
            "payment_capture": 1,
            "notes": {
                "registration_id": order_data.registration_id
            }
        })
        
        # Update registration with order_id
        await db.registrations.update_one(
            {"id": order_data.registration_id},
            {"$set": {"order_id": order["id"]}}
        )
        
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": razorpay_key_id
        }
    except Exception as e:
        logging.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

@api_router.post("/verify-payment")
async def verify_payment(payment_data: PaymentVerification):
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    try:
        # Verify signature
        message = f"{payment_data.razorpay_order_id}|{payment_data.razorpay_payment_id}"
        generated_signature = hmac.new(
            razorpay_key_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != payment_data.razorpay_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Update registration with payment details
        await db.registrations.update_one(
            {"id": payment_data.registration_id},
            {
                "$set": {
                    "payment_status": "completed",
                    "payment_id": payment_data.razorpay_payment_id
                }
            }
        )
        
        return {"status": "success", "message": "Payment verified successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment verification failed")

@api_router.post("/contact", response_model=ContactMessage)
async def submit_contact(input_data: ContactMessageCreate):
    contact = ContactMessage(**input_data.model_dump())
    
    doc = contact.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.contact_messages.insert_one(doc)
    return contact

@api_router.get("/contacts", response_model=List[ContactMessage])
async def get_contacts():
    contacts = await db.contact_messages.find({}, {"_id": 0}).to_list(1000)
    
    for contact in contacts:
        if isinstance(contact.get('created_at'), str):
            contact['created_at'] = datetime.fromisoformat(contact['created_at'])
    
    return contacts

@api_router.get("/registrations", response_model=List[Registration])
async def get_registrations():
    registrations = await db.registrations.find({}, {"_id": 0}).to_list(1000)
    
    for reg in registrations:
        if isinstance(reg.get('created_at'), str):
            reg['created_at'] = datetime.fromisoformat(reg['created_at'])
    
    return registrations

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
