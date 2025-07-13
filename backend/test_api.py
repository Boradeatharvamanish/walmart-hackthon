#!/usr/bin/env python3
"""
Test script for backend API endpoints
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a specific endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"🔍 Testing {method} {endpoint}")
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Success: {result.get('success', 'N/A')}")
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                return result
            except json.JSONDecodeError:
                print(f"📄 Response: {response.text[:200]}...")
                return None
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - Is the server running on {BASE_URL}?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Test all API endpoints"""
    print("🧪 Testing Backend API Endpoints")
    print("=" * 50)
    
    # Test health check first
    print("\n1. Testing Health Check")
    test_endpoint("/health")
    
    # Test Firebase debug
    print("\n2. Testing Firebase Debug")
    test_endpoint("/debug/firebase")
    
    # Test dashboard
    print("\n3. Testing Dashboard")
    test_endpoint("/api/dashboard")
    
    # Test orders
    print("\n4. Testing Orders")
    test_endpoint("/api/orders")
    
    # Test picking status
    print("\n5. Testing Picking Status")
    test_endpoint("/api/picking/status")
    
    # Test delivery status
    print("\n6. Testing Delivery Status")
    test_endpoint("/api/delivery/status")
    
    # Test picked orders
    print("\n7. Testing Picked Orders")
    test_endpoint("/api/delivery/picked-orders")
    
    print("\n" + "=" * 50)
    print("✅ API Testing Complete")

if __name__ == "__main__":
    main() 