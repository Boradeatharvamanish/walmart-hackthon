#!/usr/bin/env python3
"""
Quick test to verify the picking manager fixes
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_picking_manager():
    """Test the picking manager endpoints"""
    print("🧪 Testing Fixed Picking Manager")
    print("=" * 40)
    
    # Test 1: Picking status
    print("1. Testing picking status...")
    try:
        response = requests.get(f"{BASE_URL}/picking/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('active_count', 0)} active, {data.get('available_slots', 0)} available")
        else:
            print(f"❌ Status error: {response.status_code}")
    except Exception as e:
        print(f"❌ Status exception: {e}")
    
    # Test 2: Available orders
    print("\n2. Testing available orders...")
    try:
        response = requests.get(f"{BASE_URL}/picking/available-orders")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Orders: {data.get('orders_in_queue', 0)} in queue")
            else:
                print(f"⚠️ Orders: {data.get('message')}")
        else:
            print(f"❌ Orders error: {response.status_code}")
    except Exception as e:
        print(f"❌ Orders exception: {e}")
    
    # Test 3: Auto-assignment
    print("\n3. Testing auto-assignment...")
    try:
        response = requests.post(f"{BASE_URL}/picking/auto-assign")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Auto-assign: {data.get('assigned_count', 0)} assigned")
            else:
                print(f"⚠️ Auto-assign: {data.get('message')}")
        else:
            print(f"❌ Auto-assign error: {response.status_code}")
    except Exception as e:
        print(f"❌ Auto-assign exception: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Test Complete!")

if __name__ == "__main__":
    test_picking_manager() 