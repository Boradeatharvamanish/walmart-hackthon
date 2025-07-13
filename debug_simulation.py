#!/usr/bin/env python3
"""
Debug script to check simulation state
"""

import firebase_admin
from firebase_admin import credentials, db
import requests
import json

# Initialize Firebase
cred = credentials.Certificate("../serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://walmart-e8353-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

BASE_URL = "http://127.0.0.1:5000"

def check_firebase_data():
    """Check current Firebase data"""
    print("🔍 Checking Firebase data...")
    
    # Check agents
    agents_ref = db.reference("delivery_agents")
    agents = agents_ref.get()
    print(f"📦 Delivery Agents: {len(agents) if agents else 0}")
    if agents:
        for agent_id, agent_data in agents.items():
            print(f"  - {agent_id}: {agent_data.get('status', 'unknown')} at {agent_data.get('current_location', 'no location')}")
    
    # Check orders
    orders_ref = db.reference("orders")
    orders = orders_ref.get()
    print(f"📋 Orders: {len(orders) if orders else 0}")
    if orders:
        status_counts = {}
        for order_id, order_data in orders.items():
            status = order_data.get('current_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"  Status counts: {status_counts}")
    
    # Check routes
    routes_ref = db.reference("optimized_routes")
    routes = routes_ref.get()
    print(f"🗺️ Optimized Routes: {len(routes) if routes else 0}")
    if routes:
        for agent_id, route_data in routes.items():
            print(f"  - {agent_id}: {len(route_data) if isinstance(route_data, list) else 'invalid'} points")

def check_api_endpoints():
    """Check API endpoints"""
    print("\n🔍 Checking API endpoints...")
    
    endpoints = [
        "/api/dashboard",
        "/api/routes/dashboard", 
        "/api/routes/simulation/status",
        "/api/delivery/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.ok:
                data = response.json()
                print(f"✅ {endpoint}: {data.get('success', False)}")
                if 'live_tracking' in data:
                    print(f"   Active agents: {len(data['live_tracking'])}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def test_simulation():
    """Test simulation start/stop"""
    print("\n🧪 Testing simulation...")
    
    # Check current status
    try:
        response = requests.get(f"{BASE_URL}/api/routes/simulation/status")
        if response.ok:
            data = response.json()
            print(f"Current simulation status: {data.get('simulation_active', False)}")
        else:
            print("Failed to get simulation status")
    except Exception as e:
        print(f"Error checking simulation status: {e}")
    
    # Try to start simulation
    try:
        response = requests.post(f"{BASE_URL}/api/routes/simulation/start")
        if response.ok:
            data = response.json()
            print(f"Start simulation result: {data}")
        else:
            print("Failed to start simulation")
    except Exception as e:
        print(f"Error starting simulation: {e}")

def generate_test_data():
    """Generate test data if needed"""
    print("\n🔧 Generating test data...")
    
    # Check if we have busy agents
    agents_ref = db.reference("delivery_agents")
    agents = agents_ref.get() or {}
    
    busy_agents = [aid for aid, adata in agents.items() if adata.get('status') == 'busy']
    
    if not busy_agents:
        print("No busy agents found. Creating test data...")
        
        # Create a test agent
        test_agent = {
            "delivery_agent_id": "test_agent_1",
            "delivery_agent_name": "Test Agent 1",
            "status": "busy",
            "current_location": {"lat": 18.5286, "lng": 73.8748},
            "order_assigned": ["order_1", "order_2"]
        }
        
        agents_ref.child("test_agent_1").set(test_agent)
        print("Created test agent: test_agent_1")
        
        # Create test orders
        orders_ref = db.reference("orders")
        test_orders = {
            "order_1": {
                "order_id": "order_1",
                "customer_name": "Test Customer 1",
                "current_status": "picked",
                "delivery_location": {"lat": 18.5204, "lng": 73.8567},
                "order_items": ["Item 1", "Item 2"]
            },
            "order_2": {
                "order_id": "order_2", 
                "customer_name": "Test Customer 2",
                "current_status": "picked",
                "delivery_location": {"lat": 18.5366, "lng": 73.8567},
                "order_items": ["Item 3", "Item 4"]
            }
        }
        
        orders_ref.update(test_orders)
        print("Created test orders")
        
        return True
    else:
        print(f"Found {len(busy_agents)} busy agents")
        return False

if __name__ == "__main__":
    print("🔍 Darkstore Simulation Debug Tool")
    print("=" * 50)
    
    check_firebase_data()
    check_api_endpoints()
    
    # Generate test data if needed
    if generate_test_data():
        print("\n🔄 Re-checking after test data generation...")
        check_firebase_data()
    
    test_simulation()
    
    print("\n✅ Debug complete!") 