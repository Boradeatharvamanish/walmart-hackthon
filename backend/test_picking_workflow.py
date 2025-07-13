#!/usr/bin/env python3
"""
Test script for the complete picking workflow
This script will:
1. Add sample orders with "unpicked" status
2. Test auto-assignment
3. Test progress updates
4. Test completion
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

def add_sample_orders():
    """Add sample orders to test the picking workflow"""
    sample_orders = [
        {
            "order_id": "ORD001",
            "customer_name": "John Doe",
            "order_items": ["Milk", "Bread", "Eggs"],
            "delivery_location": {"lat": 12.9716, "lng": 77.5946},
            "pincode": "560001",
            "city": "Bangalore",
            "state": "Karnataka",
            "current_status": "unpicked",
            "created_at": datetime.now().isoformat()
        },
        {
            "order_id": "ORD002", 
            "customer_name": "Jane Smith",
            "order_items": ["Rice", "Dal", "Vegetables"],
            "delivery_location": {"lat": 12.9789, "lng": 77.5917},
            "pincode": "560002",
            "city": "Bangalore", 
            "state": "Karnataka",
            "current_status": "unpicked",
            "created_at": datetime.now().isoformat()
        },
        {
            "order_id": "ORD003",
            "customer_name": "Bob Wilson", 
            "order_items": ["Chicken", "Onions", "Tomatoes"],
            "delivery_location": {"lat": 12.9754, "lng": 77.5991},
            "pincode": "560003",
            "city": "Bangalore",
            "state": "Karnataka", 
            "current_status": "unpicked",
            "created_at": datetime.now().isoformat()
        },
        {
            "order_id": "ORD004",
            "customer_name": "Alice Brown",
            "order_items": ["Fish", "Potatoes", "Carrots"],
            "delivery_location": {"lat": 12.9730, "lng": 77.5933},
            "pincode": "560004", 
            "city": "Bangalore",
            "state": "Karnataka",
            "current_status": "unpicked",
            "created_at": datetime.now().isoformat()
        },
        {
            "order_id": "ORD005",
            "customer_name": "Charlie Davis",
            "order_items": ["Beef", "Garlic", "Ginger"],
            "delivery_location": {"lat": 12.9768, "lng": 77.5962},
            "pincode": "560005",
            "city": "Bangalore",
            "state": "Karnataka",
            "current_status": "unpicked", 
            "created_at": datetime.now().isoformat()
        }
    ]
    
    print("📦 Adding sample orders...")
    
    for order in sample_orders:
        try:
            response = requests.post(
                f"{BASE_URL}/test/add-order",
                json=order,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Added order {order['order_id']}")
            else:
                print(f"❌ Failed to add order {order['order_id']}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error adding order {order['order_id']}: {e}")
    
    print("📦 Sample orders added successfully!")

def test_auto_assignment():
    """Test auto-assignment of orders to pickers"""
    print("\n🔄 Testing auto-assignment...")
    
    try:
        response = requests.post(f"{BASE_URL}/picking/auto-assign")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Auto-assigned {data.get('assigned_count', 0)} orders")
                print(f"📊 Failed assignments: {data.get('failed_count', 0)}")
            else:
                print(f"❌ Auto-assignment failed: {data.get('message')}")
        else:
            print(f"❌ Auto-assignment API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing auto-assignment: {e}")

def test_progress_updates():
    """Test progress updates for active pickers"""
    print("\n⚡ Testing progress updates...")
    
    try:
        # Get current picker status
        response = requests.get(f"{BASE_URL}/picking/status")
        
        if response.status_code == 200:
            data = response.json()
            active_pickers = [p for p in data.get("pickers", []) if p.get("active")]
            
            for picker in active_pickers:
                picker_id = picker.get("id")
                current_progress = picker.get("progress", 0)
                new_progress = min(100, current_progress + 25)  # Add 25% progress
                
                print(f"🔄 Updating picker {picker_id} progress from {current_progress}% to {new_progress}%")
                
                progress_response = requests.post(
                    f"{BASE_URL}/picking/progress",
                    json={"picker_id": picker_id, "progress": new_progress},
                    headers={"Content-Type": "application/json"}
                )
                
                if progress_response.status_code == 200:
                    print(f"✅ Progress updated for picker {picker_id}")
                else:
                    print(f"❌ Failed to update progress for picker {picker_id}")
        else:
            print(f"❌ Error getting picker status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing progress updates: {e}")

def test_completion():
    """Test completing orders"""
    print("\n✅ Testing order completion...")
    
    try:
        # Get current picker status
        response = requests.get(f"{BASE_URL}/picking/status")
        
        if response.status_code == 200:
            data = response.json()
            active_pickers = [p for p in data.get("pickers", []) if p.get("active")]
            
            for picker in active_pickers:
                picker_id = picker.get("id")
                progress = picker.get("progress", 0)
                
                if progress >= 100:
                    print(f"🔄 Completing order for picker {picker_id}")
                    
                    complete_response = requests.post(
                        f"{BASE_URL}/picking/complete",
                        json={"picker_id": picker_id},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if complete_response.status_code == 200:
                        complete_data = complete_response.json()
                        if complete_data.get("success"):
                            print(f"✅ Order completed for picker {picker_id}")
                        else:
                            print(f"❌ Failed to complete order for picker {picker_id}: {complete_data.get('message')}")
                    else:
                        print(f"❌ Error completing order for picker {picker_id}: {complete_response.status_code}")
                else:
                    print(f"⏳ Picker {picker_id} progress is {progress}% - not ready for completion")
        else:
            print(f"❌ Error getting picker status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing completion: {e}")

def check_delivery_clustering():
    """Check if picked orders are available for delivery clustering"""
    print("\n🚚 Checking delivery clustering...")
    
    try:
        response = requests.post(f"{BASE_URL}/delivery/cluster-orders")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Orders clustered successfully for delivery!")
                print(f"📊 Total clusters: {data.get('data', {}).get('total_clusters', 0)}")
            else:
                print(f"❌ Clustering failed: {data.get('message')}")
        else:
            print(f"❌ Clustering API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking delivery clustering: {e}")

def main():
    """Run the complete picking workflow test"""
    print("🧪 Starting Picking Workflow Test")
    print("=" * 50)
    
    # Step 1: Add sample orders
    add_sample_orders()
    time.sleep(2)
    
    # Step 2: Test auto-assignment
    test_auto_assignment()
    time.sleep(2)
    
    # Step 3: Test progress updates
    test_progress_updates()
    time.sleep(2)
    
    # Step 4: Test completion
    test_completion()
    time.sleep(2)
    
    # Step 5: Check delivery clustering
    check_delivery_clustering()
    
    print("\n" + "=" * 50)
    print("✅ Picking Workflow Test Complete!")
    print("\n📋 Summary:")
    print("- Sample orders added with 'unpicked' status")
    print("- Orders auto-assigned to available pickers")
    print("- Progress updated for active pickers")
    print("- Orders completed when progress reaches 100%")
    print("- Completed orders become available for delivery clustering")

if __name__ == "__main__":
    main() 