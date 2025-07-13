#!/usr/bin/env python3
"""
Initialize sample data in Firebase for testing
"""

import firebase_admin
from firebase_admin import credentials, db
import json
import os
from datetime import datetime, timedelta
import random

def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            return True
            
        # Initialize Firebase
        database_url = "https://walmart-e8353-default-rtdb.asia-southeast1.firebasedatabase.app"
        
        # Try to find service account key in different locations
        service_account_files = [
            "../serviceAccountKey.json",  # Parent directory
            "serviceAccountKey.json",     # Current directory
            "firebase-service-account.json",
            "service-account-key.json",
        ]
        
        for key_file in service_account_files:
            if os.path.exists(key_file):
                print(f"🔑 Using {key_file}")
                cred = credentials.Certificate(key_file)
                firebase_admin.initialize_app(cred, {"databaseURL": database_url})
                print("✅ Firebase initialized successfully")
                return True
                
        print("❌ No service account key found")
        print("Looking for service account key in:")
        for key_file in service_account_files:
            print(f"  - {key_file} ({'exists' if os.path.exists(key_file) else 'not found'})")
        return False
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False

def create_sample_orders():
    """Create sample orders in Firebase"""
    try:
        orders_ref = db.reference("orders")
        
        # Sample order data with proper statuses
        sample_orders = {
            "ORD1349": {
                "order_id": "ORD1349",
                "order_items": ["Cake", "Curd", "Milk", "Biscuits", "Butter"],
                "delivery_location": {"lat": 40.7128, "lng": -74.0060},
                "current_status": "Unpicked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD2768": {
                "order_id": "ORD2768", 
                "order_items": ["Chips", "Cheese", "Curd"],
                "delivery_location": {"lat": 40.7589, "lng": -73.9851},
                "current_status": "Picked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD3524": {
                "order_id": "ORD3524",
                "order_items": ["Cheese", "Biscuits", "Cake", "Muffins", "Butter"],
                "delivery_location": {"lat": 40.7505, "lng": -73.9934},
                "current_status": "Unpicked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD4252": {
                "order_id": "ORD4252",
                "order_items": ["Curd", "Bread", "Butter", "Muffins"],
                "delivery_location": {"lat": 40.7614, "lng": -73.9776},
                "current_status": "Picked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD6306": {
                "order_id": "ORD6306",
                "order_items": ["Namkeen", "Cake"],
                "delivery_location": {"lat": 40.7484, "lng": -73.9857},
                "current_status": "Delivered",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD6508": {
                "order_id": "ORD6508",
                "order_items": ["Milk", "Muffins", "Namkeen", "Butter", "Chips"],
                "delivery_location": {"lat": 40.7128, "lng": -74.0060},
                "current_status": "Unpicked",
                "sla": "Delayed",
                "created_at": datetime.now().isoformat()
            },
            "ORD6780": {
                "order_id": "ORD6780",
                "order_items": ["Muffins", "Cake", "Namkeen", "Chips"],
                "delivery_location": {"lat": 40.7589, "lng": -73.9851},
                "current_status": "Picked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD8072": {
                "order_id": "ORD8072",
                "order_items": ["Biscuits", "Milk", "Chips", "Cheese", "Bread"],
                "delivery_location": {"lat": 40.7505, "lng": -73.9934},
                "current_status": "Unpicked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD8543": {
                "order_id": "ORD8543",
                "order_items": ["Milk", "Bread", "Cheese", "Muffins", "Biscuits"],
                "delivery_location": {"lat": 40.7614, "lng": -73.9776},
                "current_status": "Delivered",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            },
            "ORD9596": {
                "order_id": "ORD9596",
                "order_items": ["Muffins", "Namkeen", "Curd", "Chips"],
                "delivery_location": {"lat": 40.7484, "lng": -73.9857},
                "current_status": "Picked",
                "sla": "On Time",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Upload to Firebase
        orders_ref.set(sample_orders)
        print(f"✅ Created {len(sample_orders)} sample orders")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample orders: {e}")
        return False

def create_sample_delivery_agents():
    """Create sample delivery agents in Firebase"""
    try:
        agents_ref = db.reference("delivery_agents")
        
        # Sample delivery agents
        sample_agents = {
            "agent_001": {
                "id": "agent_001",
                "name": "John Smith",
                "phone": "+1-555-0101",
                "status": "available",
                "current_location": {
                    "lat": 40.7128,
                    "lng": -74.0060,
                    "address": "Dark Store Location"
                },
                "order_assigned": []
            },
            "agent_002": {
                "id": "agent_002", 
                "name": "Sarah Johnson",
                "phone": "+1-555-0102",
                "status": "available",
                "current_location": {
                    "lat": 40.7128,
                    "lng": -74.0060,
                    "address": "Dark Store Location"
                },
                "order_assigned": []
            },
            "agent_003": {
                "id": "agent_003",
                "name": "Mike Davis",
                "phone": "+1-555-0103",
                "status": "busy",
                "current_location": {
                    "lat": 40.7589,
                    "lng": -73.9851,
                    "address": "Delivery Location"
                },
                "order_assigned": ["ORD-003"]
            },
            "agent_004": {
                "id": "agent_004",
                "name": "Lisa Wilson",
                "phone": "+1-555-0104",
                "status": "available",
                "current_location": {
                    "lat": 40.7128,
                    "lng": -74.0060,
                    "address": "Dark Store Location"
                },
                "order_assigned": []
            },
            "agent_005": {
                "id": "agent_005",
                "name": "Tom Brown",
                "phone": "+1-555-0105",
                "status": "busy",
                "current_location": {
                    "lat": 40.7505,
                    "lng": -73.9934,
                    "address": "Delivery Location"
                },
                "order_assigned": ["ORD-005"]
            }
        }
        
        # Upload to Firebase
        agents_ref.set(sample_agents)
        print(f"✅ Created {len(sample_agents)} sample delivery agents")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample delivery agents: {e}")
        return False

def main():
    """Initialize sample data"""
    print("🚀 Initializing Sample Data")
    print("=" * 50)
    
    # Initialize Firebase
    if not initialize_firebase():
        print("❌ Cannot proceed without Firebase connection")
        return
    
    # Create sample data
    print("\n📦 Creating sample orders...")
    create_sample_orders()
    
    print("\n🚚 Creating sample delivery agents...")
    create_sample_delivery_agents()
    
    print("\n" + "=" * 50)
    print("✅ Sample data initialization complete!")
    print("💡 You can now test the dashboard with real data")

if __name__ == "__main__":
    main() 