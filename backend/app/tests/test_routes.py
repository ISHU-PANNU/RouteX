from app.core.routing_engine import solve_tsp_2opt, calculate_tour_cost
from app.models.shipment import ShipmentStatus

def test_tsp_2opt_solver():
    # Cost matrix for 4 nodes (index 0 is depot, 1, 2, 3 are stops)
    # 0 -> 1: 10, 0 -> 2: 15, 0 -> 3: 20
    cost_matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0]
    ]
    
    tour, cost = solve_tsp_2opt(cost_matrix)
    # The solver must find a tour starting at 0, visiting 1, 2, 3 once, and returning to 0
    assert tour[0] == 0
    assert tour[-1] == 0
    assert len(tour) == 5 # [0, v1, v2, v3, 0]
    assert set(tour) == {0, 1, 2, 3}
    assert cost == calculate_tour_cost(tour, cost_matrix)

def test_route_optimization_and_assignment_endpoint(client, test_users, customer_headers, admin_headers):
    # 1. Book shipments
    booking_1 = {
        "weight": 5.0,
        "length_cm": 15.0,
        "width_cm": 15.0,
        "height_cm": 10.0,
        "description": "Book A",
        "pickup_address": "123 Pickup SF Road, San Francisco, CA",
        "delivery_address": "456 Delivery SF Way, San Francisco, CA",
        "receiver_name": "John Doe",
        "receiver_phone": "+15551234",
        "receiver_email": "john.doe@example.com"
    }
    booking_2 = {
        "weight": 2.5,
        "length_cm": 20.0,
        "width_cm": 10.0,
        "height_cm": 5.0,
        "description": "Book B",
        "pickup_address": "123 Pickup SF Road, San Francisco, CA",
        "delivery_address": "789 Mission St Road, San Francisco, CA",
        "receiver_name": "Jane Smith",
        "receiver_phone": "+15555678",
        "receiver_email": "jane.smith@example.com"
    }
    
    res1 = client.post("/api/v1/shipments/book", json=booking_1, headers=customer_headers)
    res2 = client.post("/api/v1/shipments/book", json=booking_2, headers=customer_headers)
    assert res1.status_code == 201
    assert res2.status_code == 201
    
    shipment_1_id = res1.json()["id"]
    shipment_2_id = res2.json()["id"]
    
    # 2. Admin assigns and optimizes route for agent
    payload = {
        "delivery_agent_id": test_users["agent"].id,
        "shipment_ids": [shipment_1_id, shipment_2_id]
    }
    
    res_opt = client.post("/api/v1/routes/optimize-and-assign", json=payload, headers=admin_headers)
    assert res_opt.status_code == 201
    opt_data = res_opt.json()
    
    assert opt_data["delivery_agent_id"] == test_users["agent"].id
    assert "route_id" in opt_data
    assert len(opt_data["sequence"]) == 2
    
    check_shipment = client.get(f"/api/v1/shipments/{shipment_1_id}", headers=admin_headers)
    assert check_shipment.json()["status"] == ShipmentStatus.ASSIGNED_TO_DELIVERY_AGENT.value

def test_route_optimization_preview_endpoint(client, test_users, customer_headers, admin_headers):
    # 1. Book shipments
    booking_1 = {
        "weight": 5.0,
        "length_cm": 15.0,
        "width_cm": 15.0,
        "height_cm": 10.0,
        "description": "Book A",
        "pickup_address": "123 Pickup SF Road, San Francisco, CA",
        "delivery_address": "456 Delivery SF Way, San Francisco, CA",
        "receiver_name": "John Doe",
        "receiver_phone": "+15551234",
        "receiver_email": "john.doe@example.com"
    }
    booking_2 = {
        "weight": 2.5,
        "length_cm": 20.0,
        "width_cm": 10.0,
        "height_cm": 5.0,
        "description": "Book B",
        "pickup_address": "123 Pickup SF Road, San Francisco, CA",
        "delivery_address": "789 Mission St Road, San Francisco, CA",
        "receiver_name": "Jane Smith",
        "receiver_phone": "+15555678",
        "receiver_email": "jane.smith@example.com"
    }
    
    res1 = client.post("/api/v1/shipments/book", json=booking_1, headers=customer_headers)
    res2 = client.post("/api/v1/shipments/book", json=booking_2, headers=customer_headers)
    assert res1.status_code == 201
    assert res2.status_code == 201
    
    shipment_1_id = res1.json()["id"]
    shipment_2_id = res2.json()["id"]
    
    # 2. Admin previews optimized route
    payload = {
        "shipment_ids": [shipment_1_id, shipment_2_id]
    }
    
    res_preview = client.post("/api/v1/routes/optimize-preview", json=payload, headers=admin_headers)
    assert res_preview.status_code == 200
    preview_data = res_preview.json()
    
    assert "depot_lat" in preview_data
    assert "depot_lng" in preview_data
    assert "depot_address" in preview_data
    assert len(preview_data["stops"]) == 2
    assert "metrics" in preview_data
    assert "original_sequence" in preview_data
    assert "optimized_sequence" in preview_data
    
    metrics = preview_data["metrics"]
    assert "original_distance_meters" in metrics
    assert "optimized_distance_meters" in metrics
    assert "distance_savings_percent" in metrics
    assert "duration_savings_percent" in metrics

