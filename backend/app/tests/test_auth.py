from app.models.user import UserRole

def test_user_registration(client):
    payload = {
        "name": "Alex Smith",
        "email": "alex.smith@example.com",
        "password": "StrongPassword99!",
        "phone": "+15550999",
        "role": "Customer"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alex.smith@example.com"
    assert data["role"] == "Customer"
    assert "id" in data

def test_registration_validation(client):
    # Invalid password (no special char or digit)
    payload = {
        "name": "Invalid",
        "email": "invalid@example.com",
        "password": "simplepassword",
        "phone": "+15550000",
        "role": "Customer"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422 # FastAPI validation exception

def test_login(client, test_users):
    payload = {
        "email": test_users["customer"].email,
        "password": test_users["password"]
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == test_users["customer"].email

def test_role_based_access_protection(client, customer_headers, admin_headers):
    # Retrieve analytics dashboard - requires Admin role
    # Case 1: Unauthorized guest
    res_guest = client.get("/api/v1/analytics/dashboard")
    assert res_guest.status_code == 401
    
    # Case 2: Customer (forbidden)
    res_cust = client.get("/api/v1/analytics/dashboard", headers=customer_headers)
    assert res_cust.status_code == 403
    
    # Case 3: Admin (success)
    res_admin = client.get("/api/v1/analytics/dashboard", headers=admin_headers)
    assert res_admin.status_code == 200
