#!/usr/bin/env python3
"""
Test script for the complete automated workflow
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_automated_workflow():
    """Test the complete automated workflow"""
    print("🧪 Testing Complete Automated Workflow")
    print("=" * 50)
    
    # Step 1: Add a test order
    print("\n1️⃣ Adding test order...")
    test_order_data = {
        "items": ["Pizza", "Coke", "Fries"],
        "customer_name": "John Doe",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411001"
    }
    
    response = requests.post(f"{BASE_URL}/test/add-order", json=test_order_data)
    if response.ok:
        data = response.json()
        order_id = data["order_id"]
        print(f"✅ Test order {order_id} added successfully")
    else:
        print("❌ Failed to add test order")
        return
    
    # Step 2: Check if order is assigned to picker
    print("\n2️⃣ Checking if order is assigned to picker...")
    time.sleep(35)  # Wait for picking monitor to run
    
    response = requests.get(f"{BASE_URL}/api/picking/status")
    if response.ok:
        data = response.json()
        print(f"📊 Picking status: {data.get('active_count', 0)} active pickers")
        
        # Check if our order is being picked
        orders = data.get('orders', {})
        if order_id in orders:
            order_status = orders[order_id].get('current_status', 'unknown')
            print(f"📦 Order {order_id} status: {order_status}")
        else:
            print(f"❌ Order {order_id} not found in picking status")
    else:
        print("❌ Failed to get picking status")
    
    # Step 3: Complete picking (simulate picker completing order)
    print("\n3️⃣ Simulating order completion by picker...")
    response = requests.post(f"{BASE_URL}/api/picking/complete", json={"picker_id": 1})
    if response.ok:
        data = response.json()
        print(f"✅ Order completed: {data.get('message', 'Unknown')}")
    else:
        print("❌ Failed to complete order")
    
    # Step 4: Check if order is assigned to delivery agent
    print("\n4️⃣ Checking if order is assigned to delivery agent...")
    time.sleep(35)  # Wait for delivery monitor to run
    
    response = requests.get(f"{BASE_URL}/api/delivery/status")
    if response.ok:
        data = response.json()
        print(f"📊 Delivery status: {data.get('data', {}).get('busy_count', 0)} busy agents")
        
        # Check if our order is being delivered
        orders_response = requests.get(f"{BASE_URL}/api/orders")
        if orders_response.ok:
            orders_data = orders_response.json()
            for order in orders_data.get('orders', []):
                if order['id'] == order_id:
                    order_status = order['status']
                    print(f"📦 Order {order_id} status: {order_status}")
                    break
    else:
        print("❌ Failed to get delivery status")
    
    print("\n✅ Automated workflow test completed!")

def check_system_status():
    """Check overall system status"""
    print("\n📊 System Status Check")
    print("-" * 30)
    
    # Check dashboard
    response = requests.get(f"{BASE_URL}/api/dashboard")
    if response.ok:
        data = response.json()
        stats = data.get('orders', {}).get('orders_by_status', {})
        print(f"📦 Orders by status: {stats}")
    else:
        print("❌ Failed to get dashboard data")
    
    # Check picking status
    response = requests.get(f"{BASE_URL}/api/picking/status")
    if response.ok:
        data = response.json()
        print(f"🛒 Active pickers: {data.get('active_count', 0)}")
    else:
        print("❌ Failed to get picking status")
    
    # Check delivery status
    response = requests.get(f"{BASE_URL}/api/delivery/status")
    if response.ok:
        data = response.json()
        delivery_data = data.get('data', {})
        print(f"🚚 Available agents: {delivery_data.get('available_count', 0)}")
        print(f"🚚 Busy agents: {delivery_data.get('busy_count', 0)}")
    else:
        print("❌ Failed to get delivery status")

if __name__ == "__main__":
    print("🚀 Darkstore Automated Workflow Test")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.ok:
            print("✅ Backend is running")
        else:
            print("❌ Backend is not responding")
            exit(1)
    except:
        print("❌ Backend is not running. Please start the backend server first.")
        exit(1)
    
    # Check system status
    check_system_status()
    
    # Run automated workflow test
    test_automated_workflow()
    
    print("\n🎉 Test completed! Check the backend logs for detailed information.") 