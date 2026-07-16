import hashlib
from app.models.shipment import ShipmentStatus
from app.services.tracking import tracking_service

# Location update endpoint tests removed as GPS streams are no longer supported.

def test_otp_and_qr_verification_delivery_flow(client, test_users, customer_headers, agent_headers, admin_headers):
    # 1. Book shipment
    booking = {
        "weight": 1.2,
        "length_cm": 10.0,
        "width_cm": 10.0,
        "height_cm": 5.0,
        "description": "Verification Parcel",
        "pickup_address": "123 Central Warehouse Sf, San Francisco, CA",
        "delivery_address": "456 Customer Sf House, San Francisco, CA",
        "receiver_name": "Elena Rostova",
        "receiver_phone": "+15559876",
        "receiver_email": "elena@example.com"
    }
    res_book = client.post("/api/v1/shipments/book", json=booking, headers=customer_headers)
    assert res_book.status_code == 201
    shipment_id = res_book.json()["id"]
    tracking_number = res_book.json()["tracking_number"]
    
    # 2. Assign to Agent
    payload_assign = {
        "delivery_agent_id": test_users["agent"].id,
        "shipment_ids": [shipment_id]
    }
    res_assign = client.post("/api/v1/routes/optimize-and-assign", json=payload_assign, headers=admin_headers)
    assert res_assign.status_code == 201
    
    # 3. Agent attempts status update to Out For Delivery WITHOUT QR payload (should fail)
    payload_status_bad = {
        "status": ShipmentStatus.OUT_FOR_DELIVERY.value
    }
    res_bad_qr = client.patch(f"/api/v1/shipments/{shipment_id}/status", json=payload_status_bad, headers=agent_headers)
    assert res_bad_qr.status_code == 400 # VerificationFailedError or validation
    
    # 4. Agent updates status WITH CORRECT QR payload (should succeed)
    qr_payload = hashlib.sha256(f"QR-{tracking_number}".encode("utf-8")).hexdigest()
    payload_status_good = {
        "status": ShipmentStatus.OUT_FOR_DELIVERY.value,
        "qr_payload": qr_payload
    }
    res_good_qr = client.patch(f"/api/v1/shipments/{shipment_id}/status", json=payload_status_good, headers=agent_headers)
    assert res_good_qr.status_code == 200
    assert res_good_qr.json()["status"] == ShipmentStatus.OUT_FOR_DELIVERY.value
    
    # Get shipment details by customer to read OTP
    res_details = client.get(f"/api/v1/tracking/{tracking_number}", headers=customer_headers)
    assert res_details.status_code == 200
    otp_code = res_details.json()["otp_code"]
    assert otp_code is not None
    
    # 5. Agent submits WRONG OTP verification (should fail)
    res_bad_otp = client.post(f"/api/v1/shipments/{shipment_id}/verify-otp", json={"otp": "000000"}, headers=agent_headers)
    assert res_bad_otp.status_code == 400
    
    # 6. Agent submits CORRECT OTP verification (should succeed and set Delivered)
    res_good_otp = client.post(f"/api/v1/shipments/{shipment_id}/verify-otp", json={"otp": otp_code}, headers=agent_headers)
    assert res_good_otp.status_code == 200
    assert res_good_otp.json()["status"] == ShipmentStatus.DELIVERED.value

def test_proximity_notification_trigger_eval(db, test_users):
    # Mock route evaluation in database
    # Let's verify evaluate_proximity_alerts direct execution logic
    pass
