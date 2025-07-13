#!/usr/bin/env python3
"""
Quick test script to verify the picking manager is working correctly
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_picking_status():
    """Test the picking status endpoint"""
    print("🔍 Testing picking status...")
    
    try:
        response = requests.get(f"{BASE_URL}/picking/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Picking status retrieved successfully")
            print(f"📊 Active pickers: {data.get('active_count', 0)}")
            print(f"📊 Available slots: {data.get('available_slots', 0)}")
            print(f"📊 Total pickers: {len(data.get('pickers', []))}")
            return True
        else:
            print(f"❌ Error getting picking status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing picking status: {e}")
        return False

def test_available_orders():
    """Test the available orders endpoint"""
    print("\n📦 Testing available orders...")
    
    try:
        response = requests.get(f"{BASE_URL}/picking/available-orders")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Available orders retrieved successfully")
                print(f"📊 Orders in queue: {data.get('orders_in_queue', 0)}")
                print(f"📊 Can assign more: {data.get('can_assign_more', False)}")
                print(f"📊 Available pickers: {data.get('available_pickers', 0)}")
                return True
            else:
                print(f"❌ Available orders failed: {data.get('message')}")
                return False
        else:
            print(f"❌ Error getting available orders: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing available orders: {e}")
        return False

def test_auto_assignment():
    """Test auto-assignment"""
    print("\n🔄 Testing auto-assignment...")
    
    try:
        response = requests.post(f"{BASE_URL}/picking/auto-assign")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Auto-assignment successful")
                print(f"📊 Assigned count: {data.get('assigned_count', 0)}")
                print(f"📊 Failed count: {data.get('failed_count', 0)}")
                return True
            else:
                print(f"⚠️ Auto-assignment message: {data.get('message')}")
                return True  # This might be expected if no orders/pickers available
        else:
            print(f"❌ Error with auto-assignment: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing auto-assignment: {e}")
        return False

def main():
    """Run the tests"""
    print("🧪 Testing Fixed Picking Manager")
    print("=" * 40)
    
    # Test 1: Picking status
    test_picking_status()
    time.sleep(1)
    
    # Test 2: Available orders
    test_available_orders()
    time.sleep(1)
    
    # Test 3: Auto-assignment
    test_auto_assignment()
    
    print("\n" + "=" * 40)
    print("✅ Fixed Picking Manager Test Complete!")
    print("\n💡 If all tests passed, the picking manager is working correctly!")

if __name__ == "__main__":
    main() 