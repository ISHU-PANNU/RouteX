import os
import sys
from datetime import datetime, timezone
import hashlib

# Ensure backend directory is in search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
import app.database.base
from app.models.user import User, UserRole
from app.models.shipment import Shipment, ShipmentStatus
from app.models.status_history import StatusHistory
from app.core import security

def seed_database():
    db = SessionLocal()
    print("Initiating database seed process...")
    
    try:
        # 1. Create Default Users if not present
        pwd = "StrongPassword99!"
        h = security.get_password_hash(pwd)
        
        users_data = [
            {
                "name": "Platform Administrator",
                "email": "admin@example.com",
                "password_hash": h,
                "phone": "+15550001",
                "role": UserRole.Admin
            },
            {
                "name": "Standard Customer",
                "email": "customer@example.com",
                "password_hash": h,
                "phone": "+15550002",
                "role": UserRole.Customer
            },
            {
                "name": "Delivery Agent Bob",
                "email": "agent@example.com",
                "password_hash": h,
                "phone": "+15550003",
                "role": UserRole.DeliveryAgent
            },
            {
                "name": "Delivery Agent Alice",
                "email": "agent2@example.com",
                "password_hash": h,
                "phone": "+15550004",
                "role": UserRole.DeliveryAgent
            }
        ]
        
        db_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                db_user = User(**u)
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                print(f"Created User: {u['name']} ({u['role'].value})")
                db_users[u["email"]] = db_user
            else:
                print(f"User already exists: {u['name']} ({u['role'].value})")
                db_users[u["email"]] = existing

        # 2. Create Unassigned Shipments booked by Customer
        customer = db_users["customer@example.com"]
        
        shipments_data = [
            {
                "tracking_number": "RP-20260715-A1B2C3D4",
                "customer_id": customer.id,
                "weight": 5.2,
                "description": "Fragile Home Electronics Kit",
                "pickup_address": "120 Main St, San Francisco, CA",
                "pickup_lat": 37.79370000,
                "pickup_lng": -122.39650000,
                "delivery_address": "450 Sutter St, San Francisco, CA",
                "delivery_lat": 37.78980000,
                "delivery_lng": -122.40860000,
                "receiver_name": "Elena Rostova",
                "receiver_phone": "+15559876",
                "receiver_email": "elena@example.com",
                "status": ShipmentStatus.ORDER_RECEIVED
            },
            {
                "tracking_number": "RP-20260715-E5F6G7H8",
                "customer_id": customer.id,
                "weight": 14.5,
                "description": "Office Documentation Binder Archiving Box",
                "pickup_address": "120 Main St, San Francisco, CA",
                "pickup_lat": 37.79370000,
                "pickup_lng": -122.39650000,
                "delivery_address": "100 Pine St, San Francisco, CA",
                "delivery_lat": 37.79240000,
                "delivery_lng": -122.39980000,
                "receiver_name": "Robert Miller",
                "receiver_phone": "+15551234",
                "receiver_email": "robert@example.com",
                "status": ShipmentStatus.ORDER_RECEIVED
            },
            {
                "tracking_number": "RP-20260715-I9J0K1L2",
                "customer_id": customer.id,
                "weight": 1.8,
                "description": "Cotton Clothing Apparel Box",
                "pickup_address": "120 Main St, San Francisco, CA",
                "pickup_lat": 37.79370000,
                "pickup_lng": -122.39650000,
                "delivery_address": "600 Montgomery St, San Francisco, CA",
                "delivery_lat": 37.79520000,
                "delivery_lng": -122.40280000,
                "receiver_name": "Charlie Davies",
                "receiver_phone": "+15554321",
                "receiver_email": "charlie@example.com",
                "status": ShipmentStatus.ORDER_RECEIVED
            },
            {
                "tracking_number": "RP-20260715-M3N4O5P6",
                "customer_id": customer.id,
                "weight": 8.0,
                "description": "Academic Textbook Set Collection",
                "pickup_address": "120 Main St, San Francisco, CA",
                "pickup_lat": 37.79370000,
                "pickup_lng": -122.39650000,
                "delivery_address": "800 Market St, San Francisco, CA",
                "delivery_lat": 37.78450000,
                "delivery_lng": -122.40740000,
                "receiver_name": "Diana Prince",
                "receiver_phone": "+15558888",
                "receiver_email": "diana@example.com",
                "status": ShipmentStatus.ORDER_RECEIVED
            }
        ]

        for s in shipments_data:
            existing = db.query(Shipment).filter(Shipment.tracking_number == s["tracking_number"]).first()
            if not existing:
                # Add QR payload seed and 6-Digit Verification OTP
                tracking = s["tracking_number"]
                qr_hash = hashlib.sha256(f"QR-{tracking}".encode("utf-8")).hexdigest()
                import random
                otp_code = "".join(random.choices("0123456789", k=6))
                
                db_shipment = Shipment(
                    qr_code_hash=qr_hash,
                    otp_code=otp_code,
                    **s
                )
                db.add(db_shipment)
                db.commit()
                db.refresh(db_shipment)
                
                # Add history log
                log = StatusHistory(
                    shipment_id=db_shipment.id,
                    status=ShipmentStatus.ORDER_RECEIVED,
                    remarks="Shipment booked successfully during database seed process."
                )
                db.add(log)
                db.commit()
                print(f"Created Shipment: {tracking} -> OTP: {otp_code} | QR: {qr_hash[:10]}...")
            else:
                print(f"Shipment already exists: {s['tracking_number']}")

        print("Database seed process completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding process: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
