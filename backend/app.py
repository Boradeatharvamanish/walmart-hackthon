from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import json
import threading
import time

# Import the separate manager classes
from picking_manager import PickingManager
from delivery_manager import DeliveryManager

app = Flask(__name__)
CORS(app)


# Enhanced Firebase initialization with detailed debugging
def initialize_firebase():
    """Enhanced Firebase initialization with detailed debugging"""
    print("🔥 INITIALIZING FIREBASE...")

    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            # Test the existing connection
            try:
                ref = db.reference("/")
                test_data = ref.get()
                print("✅ Existing Firebase connection is working")
                return True
            except Exception as e:
                print(f"❌ Existing Firebase connection failed: {e}")
                # Clean up and reinitialize
                firebase_admin.delete_app(firebase_admin.get_app())

        database_url = (
            "https://walmart-e8353-default-rtdb.asia-southeast1.firebasedatabase.app"
        )
        print(f"🔗 Database URL: {database_url}")

        # Debug current directory and files
        print(f"📁 Current directory: {os.getcwd()}")
        json_files = [f for f in os.listdir(".") if f.endswith(".json")]
        print(f"📁 JSON files in directory: {json_files}")

        # Option 1: Try service account key files in order of preference
        service_account_files = [
            "serviceAccountKey.json",
            "firebase-service-account.json",
            "service-account-key.json",
            "firebase-adminsdk.json",  # Common alternative name
        ]

        for key_file in service_account_files:
            if os.path.exists(key_file):
                print(f"🔑 Found {key_file}, attempting to use it...")

                try:
                    # First, validate the JSON file
                    with open(key_file, "r") as f:
                        cred_data = json.load(f)

                    # Check for required fields
                    required_fields = ["private_key", "client_email", "project_id"]
                    missing_fields = [
                        field for field in required_fields if field not in cred_data
                    ]

                    if missing_fields:
                        print(
                            f"❌ {key_file} is missing required fields: {missing_fields}"
                        )
                        continue

                    print(f"✅ {key_file} has all required fields")
                    print(f"🆔 Project ID: {cred_data.get('project_id')}")

                    # Initialize Firebase
                    cred = credentials.Certificate(key_file)
                    firebase_admin.initialize_app(cred, {"databaseURL": database_url})

                    print(f"✅ Firebase initialized successfully with {key_file}")

                    # Test the connection
                    print("🧪 Testing database connection...")
                    ref = db.reference("/")
                    test_data = ref.get()

                    if test_data is not None:
                        print(f"✅ Database connection successful!")
                        if isinstance(test_data, dict):
                            print(f"📊 Root database keys: {list(test_data.keys())}")
                        else:
                            print(f"📊 Database data type: {type(test_data)}")
                        return True
                    else:
                        print(
                            "⚠️  Database connection successful but database appears empty"
                        )
                        return True

                except json.JSONDecodeError as e:
                    print(f"❌ {key_file} is not valid JSON: {e}")
                    continue
                except FileNotFoundError:
                    print(f"❌ {key_file} not found (this shouldn't happen)")
                    continue
                except Exception as e:
                    print(f"❌ Failed to initialize Firebase with {key_file}: {e}")
                    print(f"   Error type: {type(e).__name__}")

                    # Clean up failed initialization
                    if firebase_admin._apps:
                        try:
                            firebase_admin.delete_app(firebase_admin.get_app())
                        except:
                            pass
                    continue

        # Option 2: Try environment variable
        google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if google_creds_path:
            print(
                f"🌍 Trying Application Default Credentials from: {google_creds_path}"
            )

            if os.path.exists(google_creds_path):
                try:
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred, {"databaseURL": database_url})
                    print(
                        "✅ Firebase initialized successfully with Application Default Credentials"
                    )

                    # Test the connection
                    print("🧪 Testing database connection...")
                    ref = db.reference("/")
                    test_data = ref.get()
                    print("✅ Database connection successful!")
                    return True

                except Exception as e:
                    print(
                        f"❌ Failed to initialize Firebase with Application Default Credentials: {e}"
                    )
            else:
                print(
                    f"❌ GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {google_creds_path}"
                )

        # If we get here, all attempts failed
        print("\n❌ ALL FIREBASE INITIALIZATION ATTEMPTS FAILED")
        print("\n💡 TROUBLESHOOTING CHECKLIST:")
        print(
            "1. ✅ Check that your service account JSON file is in the project root directory"
        )
        print(
            "2. ✅ Verify the JSON file is valid and contains private_key, client_email, project_id"
        )
        print("3. ✅ Ensure the database URL is correct for your Firebase project")
        print("4. ✅ Confirm your Firebase project has Realtime Database enabled")
        print("5. ✅ Check that your service account has Database Admin permissions")
        print("6. ✅ Try downloading a fresh service account key from Firebase Console")
        print("7. ✅ Verify you're using the correct Firebase project")
        print("8. ✅ Check your internet connection and firewall settings")

        return False

    except Exception as e:
        print(f"❌ Unexpected error during Firebase initialization: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False


def test_firebase_connection():
    """Test Firebase connection with detailed feedback"""
    print("\n🧪 TESTING FIREBASE CONNECTION...")

    try:
        # Test basic connection
        ref = db.reference("/")
        root_data = ref.get()
        print("✅ Basic connection test passed")

        # Test specific paths your app uses
        test_paths = ["/orders", "/delivery_agents", "/pickers"]

        for path in test_paths:
            try:
                ref = db.reference(path)
                data = ref.get()
                count = len(data) if data and isinstance(data, dict) else 0
                print(f"✅ {path}: {count} items")
            except Exception as e:
                print(f"⚠️  {path}: Error accessing - {e}")

        return True

    except Exception as e:
        print(f"❌ Firebase connection test failed: {e}")
        return False


def start_delivery_monitoring():
    """Start monitoring for picked orders in a separate thread"""
    print("🚚 Starting delivery monitoring thread...")

    def monitor_thread():
        try:
            if firebase_initialized and delivery_manager:
                # Start the watcher with 30-second intervals
                delivery_manager.watch_and_assign(interval=30)
            else:
                print(
                    "❌ Cannot start monitoring - Firebase not initialized or delivery manager not available"
                )
        except Exception as e:
            print(f"❌ Error in delivery monitoring thread: {e}")
            import traceback

            traceback.print_exc()

    # Start monitoring in a daemon thread
    monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
    monitor_thread.start()
    print("✅ Delivery monitoring thread started")


# Initialize Firebase
print("🚀 Starting Firebase initialization...")
firebase_initialized = initialize_firebase()

if firebase_initialized:
    print("🎉 Firebase initialization completed successfully!")
    test_firebase_connection()
else:
    print("⚠️  Firebase initialization failed - some features may not work")

# Initialize managers
print("📋 Initializing managers...")
picking_manager = PickingManager()
delivery_manager = DeliveryManager()
print("✅ Managers initialized successfully")

# Start delivery monitoring if Firebase is initialized
if firebase_initialized:
    start_delivery_monitoring()


@app.route("/")
def home():
    firebase_status = "✅ Connected" if firebase_initialized else "❌ Not Connected"
    return f"Flask backend is running with Picking Management and Delivery Management. Firebase: {firebase_status}"


# === PICKING MANAGEMENT ROUTES ===
@app.route("/api/picking/status", methods=["GET"])
def get_picking_status():
    """Get current picking status"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        return jsonify(
            {"success": True, "data": picking_manager.get_picker_assignments()}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/available-orders", methods=["GET"])
def get_available_orders():
    """Get list of available orders for picking"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        result = picking_manager.get_next_available_order()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/assign", methods=["POST"])
def assign_order():
    """Assign an order to a picker"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        data = request.get_json()
        order_id = data.get(
            "order_id"
        )  # Optional - if not provided, gets next available
        picker_id = data.get("picker_id")  # Optional

        result = picking_manager.assign_order_to_picker(order_id, picker_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/progress", methods=["POST"])
def update_progress():
    """Update picker progress"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        data = request.get_json()
        picker_id = data.get("picker_id")
        progress = data.get("progress")

        if picker_id is None or progress is None:
            return (
                jsonify(
                    {"success": False, "error": "picker_id and progress are required"}
                ),
                400,
            )

        result = picking_manager.update_picker_progress(picker_id, progress)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/complete", methods=["POST"])
def complete_picking():
    """Complete picking for a picker and update Firebase"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        data = request.get_json()
        picker_id = data.get("picker_id")

        if picker_id is None:
            return jsonify({"success": False, "error": "picker_id is required"}), 400

        result = picking_manager.complete_picking(picker_id)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/auto-assign", methods=["POST"])
def auto_assign_orders():
    """Auto-assign available orders to available pickers with proper queue management"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get current status
        status = picking_manager.get_next_available_order()
        if not status["success"]:
            return jsonify(status), 500

        available_orders = status["available_orders"]
        available_pickers = status["available_pickers"]

        if available_pickers == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No available pickers for assignment",
                        "status": status,
                    }
                ),
                400,
            )

        if len(available_orders) == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No orders available for assignment",
                        "status": status,
                    }
                ),
                400,
            )

        # Determine how many orders to assign
        orders_to_assign = min(len(available_orders), available_pickers)

        assignments = []
        failed_assignments = []

        # Assign orders one by one
        for i in range(orders_to_assign):
            order_id = available_orders[i]["order_id"]
            result = picking_manager.assign_order_to_picker(order_id)

            if result["success"]:
                assignments.append(result)
            else:
                failed_assignments.append(
                    {"order_id": order_id, "error": result["message"]}
                )

        # Get updated status
        final_status = picking_manager.get_next_available_order()

        return jsonify(
            {
                "success": True,
                "assignments": assignments,
                "failed_assignments": failed_assignments,
                "assigned_count": len(assignments),
                "failed_count": len(failed_assignments),
                "final_status": (
                    final_status["data"] if final_status["success"] else None
                ),
                "message": f"Successfully assigned {len(assignments)} orders to pickers",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/reset", methods=["POST"])
def reset_all_pickers():
    """Reset all picker assignments and update Firebase statuses"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        result = picking_manager.reset_all_pickers()

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === DELIVERY MANAGEMENT ROUTES ===
@app.route("/api/delivery/status", methods=["GET"])
def get_delivery_status():
    """Get current status of all delivery agents"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        agents_ref = db.reference("delivery_agents")
        all_agents = agents_ref.get() or {}

        available_agents = []
        busy_agents = []

        for agent_id, agent_data in all_agents.items():
            agent_info = {
                "id": agent_data.get("delivery_agent_id"),
                "name": agent_data.get("delivery_agent_name"),
                "status": agent_data.get("status"),
                "current_location": agent_data.get("current_location", {}),
                "order_assigned": agent_data.get("order_assigned", []),
            }

            if agent_data.get("status") == "available":
                available_agents.append(agent_info)
            else:
                busy_agents.append(agent_info)

        return jsonify(
            {
                "success": True,
                "data": {
                    "available_agents": available_agents,
                    "busy_agents": busy_agents,
                    "total_agents": len(all_agents),
                    "available_count": len(available_agents),
                    "busy_count": len(busy_agents),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/picked-orders", methods=["GET"])
def get_picked_orders():
    """Get orders that are picked and ready for delivery"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        orders_ref = db.reference("orders")
        all_orders = orders_ref.get() or {}

        picked_orders = []
        for order_id, order_data in all_orders.items():
            if order_data.get("current_status") == "Picked":
                order_info = {
                    "order_id": order_data.get("order_id"),
                    "order_items": order_data.get("order_items", []),
                    "delivery_location": order_data.get("delivery_location", {}),
                    "pincode": order_data.get("pincode", ""),
                    "current_status": order_data.get("current_status"),
                }
                picked_orders.append(order_info)

        return jsonify(
            {
                "success": True,
                "data": {
                    "picked_orders": picked_orders,
                    "total_count": len(picked_orders),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/clusters", methods=["GET"])
def get_delivery_clusters():
    """Get current delivery clusters"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        if not hasattr(delivery_manager, "clusters"):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No clusters available. Run clustering first.",
                    }
                ),
                400,
            )

        return jsonify(
            {
                "success": True,
                "data": {
                    "clusters": delivery_manager.clusters,
                    "total_clusters": len(delivery_manager.clusters),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/cluster-orders", methods=["POST"])
def cluster_orders():
    """Manually trigger order clustering"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Refresh data first
        delivery_manager.available_agents = []
        delivery_manager.orders_to_assign = []
        delivery_manager._load_available_agents()
        delivery_manager._load_picked_orders()

        if not delivery_manager.orders_to_assign:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No picked orders available for clustering",
                    }
                ),
                400,
            )

        if not delivery_manager.available_agents:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No available delivery agents for clustering",
                    }
                ),
                400,
            )

        # Perform clustering
        delivery_manager.cluster_orders_by_location()

        return jsonify(
            {
                "success": True,
                "message": "Orders clustered successfully",
                "data": {
                    "clusters": delivery_manager.clusters,
                    "total_clusters": len(delivery_manager.clusters),
                    "available_agents": len(delivery_manager.available_agents),
                    "orders_to_assign": len(delivery_manager.orders_to_assign),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/assign-clusters", methods=["POST"])
def assign_clusters():
    """Manually assign clusters to delivery agents"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        if not hasattr(delivery_manager, "clusters") or not delivery_manager.clusters:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No clusters available. Run clustering first.",
                    }
                ),
                400,
            )

        # Assign clusters to agents
        delivery_manager.assign_clusters_to_agents()

        return jsonify(
            {
                "success": True,
                "message": "Clusters assigned to delivery agents successfully",
                "data": {
                    "assigned_clusters": len(delivery_manager.clusters),
                    "available_agents": len(delivery_manager.available_agents),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/agent/<agent_id>/orders", methods=["GET"])
def get_agent_orders(agent_id):
    """Get orders assigned to a specific delivery agent"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        agent_ref = db.reference(f"delivery_agents/{agent_id}")
        agent_data = agent_ref.get()

        if not agent_data:
            return (
                jsonify({"success": False, "message": f"Agent {agent_id} not found"}),
                404,
            )

        assigned_orders = agent_data.get("order_assigned", [])

        # Get detailed order information
        orders_info = []
        if assigned_orders:
            orders_ref = db.reference("orders")
            for order_id in assigned_orders:
                order_data = orders_ref.child(order_id).get()
                if order_data:
                    orders_info.append({"order_id": order_id, "order_data": order_data})

        return jsonify(
            {
                "success": True,
                "data": {
                    "agent_id": agent_id,
                    "agent_name": agent_data.get("delivery_agent_name"),
                    "status": agent_data.get("status"),
                    "assigned_orders": assigned_orders,
                    "orders_info": orders_info,
                    "total_orders": len(assigned_orders),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/monitoring/start", methods=["POST"])
def start_monitoring():
    """Start delivery monitoring (if not already running)"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Check if monitoring is already running
        # For now, we'll just return success as the monitoring starts automatically
        return jsonify(
            {
                "success": True,
                "message": "Delivery monitoring is active",
                "monitoring_interval": 30,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/monitoring/status", methods=["GET"])
def get_monitoring_status():
    """Get delivery monitoring status"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        return jsonify(
            {
                "success": True,
                "data": {
                    "monitoring_active": True,
                    "firebase_connected": firebase_initialized,
                    "last_check": datetime.now().isoformat(),
                    "available_agents": len(delivery_manager.available_agents),
                    "orders_to_assign": len(delivery_manager.orders_to_assign),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delivery/refresh", methods=["POST"])
def refresh_delivery_data():
    """Refresh delivery agents and orders data"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Refresh data
        delivery_manager.available_agents = []
        delivery_manager.orders_to_assign = []
        delivery_manager._load_available_agents()
        delivery_manager._load_picked_orders()

        return jsonify(
            {
                "success": True,
                "message": "Delivery data refreshed successfully",
                "data": {
                    "available_agents": len(delivery_manager.available_agents),
                    "orders_to_assign": len(delivery_manager.orders_to_assign),
                    "agents": delivery_manager.available_agents,
                    "orders": delivery_manager.orders_to_assign,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === GENERAL UTILITY ROUTES ===
@app.route("/api/orders", methods=["GET"])
def get_all_orders():
    """Get all orders from Firebase"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        orders_ref = db.reference("orders")
        orders = orders_ref.get() or {}

        return jsonify({"success": True, "orders": orders, "total_orders": len(orders)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order_details(order_id):
    """Get details of a specific order"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        order_ref = db.reference(f"orders/{order_id}")
        order_data = order_ref.get()

        if not order_data:
            return (
                jsonify({"success": False, "error": f"Order {order_id} not found"}),
                404,
            )

        return jsonify({"success": True, "order_id": order_id, "data": order_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get picking status
        picking_status = picking_manager.get_picker_assignments()

        # Get delivery status
        delivery_status_response = get_delivery_status()
        delivery_status = (
            delivery_status_response[0].get_json()
            if delivery_status_response[1] == 200
            else {}
        )

        # Get orders summary
        orders_summary = {"total_orders": 0, "firebase_connected": firebase_initialized}
        if firebase_initialized:
            try:
                orders_ref = db.reference("orders")
                orders = orders_ref.get() or {}
                orders_summary = {
                    "total_orders": len(orders),
                    "firebase_connected": True,
                    "orders_by_status": {},
                }

                # Count orders by status
                for order_data in orders.values():
                    status = order_data.get("current_status", "unknown")
                    orders_summary["orders_by_status"][status] = (
                        orders_summary["orders_by_status"].get(status, 0) + 1
                    )

            except Exception as e:
                orders_summary["firebase_error"] = str(e)

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "picking": picking_status,
                "delivery": delivery_status,
                "orders": orders_summary,
                "monitoring": {
                    "active": True,
                    "available_agents": len(delivery_manager.available_agents),
                    "orders_to_assign": len(delivery_manager.orders_to_assign),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/debug/firebase", methods=["GET"])
def debug_firebase():
    """Enhanced Firebase debug endpoint"""
    try:
        debug_info = {
            "firebase_initialized": firebase_initialized,
            "firebase_apps_count": len(firebase_admin._apps),
            "current_directory": os.getcwd(),
            "json_files": [f for f in os.listdir(".") if f.endswith(".json")],
            "environment_credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            "database_url": "https://walmart-e8353-default-rtdb.asia-southeast1.firebasedatabase.app",
        }

        if not firebase_initialized:
            debug_info["error"] = "Firebase not initialized"
            debug_info["suggestions"] = [
                "Check if serviceAccountKey.json exists in project root",
                "Verify Firebase database URL is correct",
                "Check service account file permissions",
                "Ensure Realtime Database is enabled in Firebase Console",
                "Verify service account has proper permissions",
            ]
            return jsonify(debug_info), 500

        # Try to connect to database
        orders_ref = db.reference("orders")
        orders = orders_ref.get()

        debug_info.update(
            {
                "success": True,
                "orders_count": len(orders) if orders else 0,
                "sample_order_keys": list(orders.keys())[:3] if orders else [],
                "database_connection": "✅ Working",
            }
        )

        return jsonify(debug_info)

    except Exception as e:
        return (
            jsonify(
                {
                    "firebase_initialized": firebase_initialized,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "firebase_apps": (
                        len(firebase_admin._apps) if firebase_admin._apps else 0
                    ),
                }
            ),
            500,
        )


# @app.route("/debug/delivery-agents", methods=["GET"])
# def debug_delivery_agents():
#     """Debug delivery agents from Firebase"""
#     try:
#         if not firebase_initialized:
#             return jsonify({"success": False, "error": "Firebase not initialized"}), 500

#         # Get delivery agents from Firebase
#         agents_ref = db.reference("delivery_agents")
#         agents = agents_ref.get()

#         return jsonify(
#             {
#                 "success": True,
#                 "firebase_agents": agents,
#                 "local_agents": delivery_manager.delivery_agents,
#                 "total_local_agents": len(delivery_manager.delivery_agents),
#             }
#         )

#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)}), 500


# === HEALTH CHECK ENDPOINT ===
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "firebase_connected": firebase_initialized,
            "services": {
                "picking_manager": "✅ Ready",
                "delivery_manager": "✅ Ready",
                "firebase": (
                    "✅ Connected" if firebase_initialized else "❌ Not Connected"
                ),
            },
        }
    )


# === MAIN APPLICATION RUNNER ===
if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    print(
        f"🔥 Firebase Status: {'✅ Connected' if firebase_initialized else '❌ Not Connected'}"
    )
    print("\n📋 Available endpoints:")
    print("  GET  /                              - Home page")
    print("  GET  /debug/firebase                - Debug Firebase connection")
    print("  GET  /debug/delivery-agents         - Debug delivery agents")
    print("")
    print("=== PICKING MANAGEMENT ===")
    print("  GET  /api/picking/status            - Get picking status")
    print("  GET  /api/picking/available-orders  - Get available orders")
    print("  POST /api/picking/assign            - Assign order to picker")
    print("  POST /api/picking/progress          - Update picker progress")
    print("  POST /api/picking/complete          - Complete picking")
    print("  POST /api/picking/auto-assign       - Auto-assign orders")
    print("  POST /api/picking/reset             - Reset all pickers")
    print("")
    print("=== DELIVERY MANAGEMENT ===")
    print("  GET  /api/delivery/status           - Get delivery status")
    print("  GET  /api/delivery/assignments      - Get delivery assignments")
    print("  GET  /api/delivery/available-orders - Get available delivery orders")
    print(
        "  POST /api/delivery/assign           - Assign orders to delivery boys (batching)"
    )
    print("  POST /api/delivery/assign-single    - Assign single order to delivery boy")
    print("  POST /api/delivery/reset            - Reset delivery assignments")
    print("  POST /api/delivery/update-status    - Update delivery status")
    print("  POST /api/delivery/complete         - Complete delivery")
    print(
        "  POST /api/delivery/refresh          - Refresh delivery agents from Firebase"
    )
    print("  GET  /api/delivery/boy/<id>/orders  - Get delivery boy orders")
    print("  GET  /api/delivery/performance      - Get delivery performance metrics")
    print("")
    print("=== UTILITY ROUTES ===")
    print("  GET  /api/orders                    - Get all orders")
    print("  GET  /api/orders/<id>               - Get order details")
    print("  GET  /api/dashboard                 - Get dashboard data")
    print("")

    if not firebase_initialized:
        print("⚠  WARNING: Firebase not initialized!")
        print("   Please ensure you have one of these files:")
        print("   - serviceAccountKey.json")
        print("   - firebase-service-account.json")
        print("   - service-account-key.json")
        print("   Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")

    app.run(debug=True, host="0.0.0.0", port=5000)
