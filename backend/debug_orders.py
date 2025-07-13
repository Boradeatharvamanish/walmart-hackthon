import firebase_admin
from firebase_admin import credentials, db
import json
import os


def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            return True

        # Initialize Firebase
        database_url = (
            "https://walmart-e8353-default-rtdb.asia-southeast1.firebasedatabase.app"
        )

        # Try to find service account key
        service_account_files = [
            "serviceAccountKey.json",
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
        return False

    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False


def debug_orders():
    """Debug order data in Firebase"""
    try:
        orders_ref = db.reference("orders")
        orders = orders_ref.get()

        print("\n📦 DEBUGGING ORDERS IN FIREBASE")
        print("=" * 50)

        if not orders:
            print("❌ No orders found in Firebase")
            return

        print(f"📊 Total orders found: {len(orders)}")
        print("\n📋 Order Details:")

        status_counts = {}

        for order_id, order_data in orders.items():
            status = order_data.get("current_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            print(f"  {order_id}:")
            print(f"    - Order ID: {order_data.get('order_id', 'N/A')}")
            print(f"    - Status: '{status}'")
            print(f"    - Items: {order_data.get('order_items', [])}")
            print(f"    - SLA: {order_data.get('sla', 'N/A')}")
            print()

        print("📈 Status Summary:")
        for status, count in status_counts.items():
            print(f"  - '{status}': {count}")

        print("\n🔍 Testing API endpoint...")
        test_api_response()

    except Exception as e:
        print(f"❌ Error debugging orders: {e}")


def test_api_response():
    """Test the dashboard API endpoint"""
    import requests

    try:
        response = requests.get("http://127.0.0.1:5000/api/dashboard", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"  - Success: {data.get('success')}")
            print(f"  - Orders: {data.get('orders', {})}")
            print(
                f"  - Orders by status: {data.get('orders', {}).get('orders_by_status', {})}"
            )
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"  Response: {response.text}")

    except Exception as e:
        print(f"❌ API Test Error: {e}")


def main():
    """Main debug function"""
    print("🔍 DEBUGGING ORDER DATA")
    print("=" * 50)

    if not initialize_firebase():
        print("❌ Cannot proceed without Firebase connection")
        return

    debug_orders()


if __name__ == "__main__":
    main()
