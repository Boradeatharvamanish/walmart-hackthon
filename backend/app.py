from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import json
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from route_optimizer import (
    generate_optimized_routes_for_busy_agents,
    generate_tsp_route,
    reroute_if_traffic,
    simulate_all_agents_movement,
    start_route_simulation,
    stop_route_simulation,
    get_enhanced_live_tracking_data,
    route_optimizer_active,
    simulate_single_agent_movement,
    DARK_STORE_LOCATION,
)

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
            "../../serviceAccountKey.json",  # Root directory (two levels up)
            "../serviceAccountKey.json",     # Parent directory
            "serviceAccountKey.json",        # Current directory
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
    """Start delivery monitoring in background thread"""
    def monitor_thread():
        try:
            print("🚚 Starting delivery monitoring thread...")
            delivery_manager.watch_and_assign(interval=30)  # Check every 30 seconds
        except Exception as e:
            print(f"❌ Error in delivery monitoring: {e}")
        finally:
            print("🛑 Delivery monitoring stopped")
    
    delivery_thread = threading.Thread(target=monitor_thread, daemon=True)
    delivery_thread.start()

def start_picking_monitoring():
    """Start picking monitoring in background thread"""
    def monitor_thread():
        try:
            print("🛒 Starting picking monitoring thread...")
            while True:
                try:
                    # Auto-assign orders to available pickers
                    status = picking_manager.get_next_available_order()
                    if status["success"] and status["can_assign_more"]:
                        print(f"[Picking Monitor] Auto-assigning orders...")
                        # Try to assign one order at a time
                        available_orders = status["available_orders"]
                        if available_orders:
                            order_id = available_orders[0]["order_id"]
                            result = picking_manager.assign_order_to_picker(order_id)
                            if result["success"]:
                                print(f"[Picking Monitor] Auto-assigned order {order_id}")
                            else:
                                print(f"[Picking Monitor] Failed to assign order {order_id}: {result['message']}")
                    else:
                        print("[Picking Monitor] No orders to assign or no available pickers")
                    
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    print(f"[Picking Monitor] Error: {e}")
                    time.sleep(30)
        except Exception as e:
            print(f"❌ Error in picking monitoring: {e}")
        finally:
            print("🛑 Picking monitoring stopped")
    
    picking_thread = threading.Thread(target=monitor_thread, daemon=True)
    picking_thread.start()


def start_route_simulation():
    """Start route simulation in background thread"""
    global route_optimizer_active, simulation_thread

    if route_optimizer_active:
        return {"success": False, "message": "Route simulation already running"}

    def run_simulation():
        global route_optimizer_active
        route_optimizer_active = True
        try:
            print("🚗 Starting route simulation...")
            simulate_all_agents_movement(step_delay=2, proximity_threshold_km=0.05)
        except Exception as e:
            print(f"❌ Error in route simulation: {e}")
        finally:
            route_optimizer_active = False
            print("🛑 Route simulation stopped")

    simulation_thread = threading.Thread(target=run_simulation, daemon=True)
    simulation_thread.start()

    return {"success": True, "message": "Route simulation started"}


def stop_route_simulation():
    """Stop route simulation"""
    global route_optimizer_active
    route_optimizer_active = False
    return {"success": True, "message": "Route simulation stopped"}


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

route_optimizer_active = False
simulation_thread = None
executor = ThreadPoolExecutor(max_workers=2)

# Start delivery monitoring if Firebase is initialized
if firebase_initialized:
    start_delivery_monitoring()
    start_picking_monitoring() # Start picking monitoring as well


@app.route("/")
def home():
    firebase_status = "✅ Connected" if firebase_initialized else "❌ Not Connected"
    return f"Flask backend is running with Picking Management and Delivery Management. Firebase: {firebase_status}"


# === PICKING MANAGEMENT ROUTES ===
@app.route("/api/picking/status", methods=["GET"])
def get_picking_status():
    """Get picker assignments and order details for frontend"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500
        assignments = picking_manager.get_picker_assignments()
        # Attach order details to each picker if active
        orders_ref = db.reference("orders")
        orders = orders_ref.get() or {}
        for picker in assignments["pickers"]:
            if picker.get("active") and picker.get("order_id"):
                order = orders.get(picker["order_id"])
                picker["order_details"] = order if order else {}
        return jsonify(assignments)
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
def update_picker_progress():
    """Update picker progress (frontend calls this to update progress bar)"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500
        data = request.get_json() or {}
        picker_id = data.get("picker_id")
        progress = data.get("progress")
        if not picker_id or progress is None:
            return jsonify({"success": False, "error": "picker_id and progress required"}), 400
        result = picking_manager.update_picker_progress(picker_id, progress)
        return jsonify(result)
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

        # Use the new auto_assign_orders method from picking manager
        result = picking_manager.auto_assign_orders()
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

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


@app.route("/api/routes/generate-all", methods=["POST"])
def generate_all_routes():
    """Generate optimized routes for all busy delivery agents"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Generate routes for all busy agents
        optimized_routes = generate_optimized_routes_for_busy_agents()

        if not optimized_routes:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No busy agents found or no routes generated",
                    }
                ),
                400,
            )

        # Store routes in Firebase for live tracking
        routes_ref = db.reference("optimized_routes")
        routes_ref.update(optimized_routes)

        return jsonify(
            {
                "success": True,
                "message": f"Generated routes for {len(optimized_routes)} agents",
                "routes": optimized_routes,
                "agents_count": len(optimized_routes),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/agent/<agent_id>", methods=["GET"])
def get_agent_route(agent_id):
    """Get optimized route for a specific agent"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get agent data
        agent_ref = db.reference(f"delivery_agents/{agent_id}")
        agent_data = agent_ref.get()

        if not agent_data:
            return (
                jsonify({"success": False, "message": f"Agent {agent_id} not found"}),
                404,
            )

        if agent_data.get("status") != "busy":
            return (
                jsonify({"success": False, "message": f"Agent {agent_id} is not busy"}),
                400,
            )

        # Get assigned orders and generate route
        assigned_orders = agent_data.get("order_assigned", [])
        if not assigned_orders:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"No orders assigned to agent {agent_id}",
                    }
                ),
                400,
            )

        # Get delivery locations
        delivery_locations = []
        for order_id in assigned_orders:
            order = db.reference(f"orders/{order_id}").get()
            if order and "delivery_location" in order:
                delivery_locations.append(order["delivery_location"])

        if not delivery_locations:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No delivery locations found for assigned orders",
                    }
                ),
                400,
            )

        # Generate route
        origin = agent_data.get("current_location", DARK_STORE_LOCATION)
        route_points = generate_tsp_route(origin, delivery_locations)

        return jsonify(
            {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent_data.get("delivery_agent_name"),
                "route_points": route_points,
                "total_points": len(route_points),
                "delivery_locations": delivery_locations,
                "assigned_orders": assigned_orders,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/reroute/<agent_id>", methods=["POST"])
def reroute_agent(agent_id):
    """Reroute an agent based on traffic conditions"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get current route from Firebase
        routes_ref = db.reference(f"optimized_routes/{agent_id}")
        old_route = routes_ref.get()

        if not old_route:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"No existing route found for agent {agent_id}",
                    }
                ),
                404,
            )

        # Get delay threshold from request
        data = request.get_json() or {}
        delay_threshold = data.get("delay_threshold_minutes", 5)

        # Reroute if traffic detected
        new_route = reroute_if_traffic(agent_id, old_route, delay_threshold)

        # Update route in Firebase
        routes_ref.set(new_route)

        route_changed = new_route != old_route

        return jsonify(
            {
                "success": True,
                "agent_id": agent_id,
                "route_changed": route_changed,
                "new_route": new_route,
                "total_points": len(new_route),
                "delay_threshold": delay_threshold,
                "message": (
                    "Route updated successfully"
                    if route_changed
                    else "No rerouting needed"
                ),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/live-tracking", methods=["GET"])
def get_live_tracking_data():
    """Get live tracking data for all delivery agents"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get all delivery agents
        agents_ref = db.reference("delivery_agents")
        all_agents = agents_ref.get() or {}

        # Get optimized routes
        routes_ref = db.reference("optimized_routes")
        all_routes = routes_ref.get() or {}

        live_tracking_data = []

        for agent_id, agent_data in all_agents.items():
            if agent_data.get("status") == "busy":
                agent_route = all_routes.get(agent_id, [])

                # Get assigned orders for delivery locations
                assigned_orders = agent_data.get("order_assigned", [])
                delivery_locations = []

                for order_id in assigned_orders:
                    order = db.reference(f"orders/{order_id}").get()
                    if order and "delivery_location" in order:
                        delivery_locations.append(
                            {
                                "order_id": order_id,
                                "location": order["delivery_location"],
                                "status": order.get("current_status", "unknown"),
                            }
                        )

                tracking_info = {
                    "agent_id": agent_data.get("delivery_agent_id"),
                    "agent_name": agent_data.get("delivery_agent_name"),
                    "current_location": agent_data.get(
                        "current_location", DARK_STORE_LOCATION
                    ),
                    "status": agent_data.get("status"),
                    "route_points": agent_route,
                    "delivery_locations": delivery_locations,
                    "assigned_orders": assigned_orders,
                    "total_deliveries": len(assigned_orders),
                }

                live_tracking_data.append(tracking_info)

        return jsonify(
            {
                "success": True,
                "live_tracking": live_tracking_data,
                "total_active_agents": len(live_tracking_data),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# NEW ENHANCED API ROUTES - ADD THESE TO YOUR app.py


@app.route("/api/routes/live-tracking-enhanced", methods=["GET"])
def get_enhanced_live_tracking():
    """Get enhanced live tracking data with route visualization"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Add debugging information
        agents_ref = db.reference("delivery_agents")
        agents_data = agents_ref.get() or {}
        busy_agents = {
            k: v for k, v in agents_data.items() if v.get("status") == "busy"
        }

        print(
            f"[API] Enhanced live tracking - Total agents: {len(agents_data)}, Busy agents: {len(busy_agents)}"
        )

        result = get_enhanced_live_tracking_data()

        # Add debugging info to response
        if result.get("success"):
            result["debug"] = {
                "total_agents": len(agents_data),
                "busy_agents": len(busy_agents),
                "busy_agent_ids": list(busy_agents.keys()),
            }

        return jsonify(result)
    except Exception as e:
        print(f"[API] Error in enhanced live tracking: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/generate-and-simulate", methods=["POST"])
def generate_and_simulate_routes():
    """Generate optimized routes and start simulation"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        print("[API] Generating and simulating routes...")

        # Generate routes for all busy agents
        optimized_routes = generate_optimized_routes_for_busy_agents()

        if not optimized_routes:
            print("[API] No busy agents found for route generation")
            return jsonify({"success": False, "message": "No busy agents found"}), 400

        # Store routes in Firebase
        routes_ref = db.reference("optimized_routes")
        routes_ref.update(optimized_routes)
        print(f"[API] Stored {len(optimized_routes)} routes in Firebase")

        # Start simulation if not already running
        if not route_optimizer_active:
            start_result = start_route_simulation()
            if not start_result["success"]:
                return jsonify(start_result), 400
            print("[API] Started route simulation")
        else:
            print("[API] Route simulation already active")

        return jsonify(
            {
                "success": True,
                "message": f"Generated and simulating routes for {len(optimized_routes)} agents",
                "routes_count": len(optimized_routes),
                "simulation_started": True,
                "routes": optimized_routes,  # Include route data for debugging
            }
        )

    except Exception as e:
        print(f"[API] Error in generate_and_simulate_routes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/simulation/start", methods=["POST"])
def start_simulation():
    """Start route simulation for all busy agents"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        result = start_route_simulation()

        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "message": "Route simulation started successfully",
                    "simulation_active": route_optimizer_active,
                }
            )
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/simulation/stop", methods=["POST"])
def stop_simulation():
    """Stop route simulation"""
    try:
        result = stop_route_simulation()

        return jsonify(
            {
                "success": True,
                "message": "Route simulation stopped",
                "simulation_active": route_optimizer_active,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/simulation/status", methods=["GET"])
def get_simulation_status():
    """Get current simulation status"""
    try:
        return jsonify(
            {
                "success": True,
                "simulation_active": route_optimizer_active,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/agent/<agent_id>/simulate", methods=["POST"])
def simulate_agent_movement(agent_id):
    """Simulate movement for a specific agent"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get simulation parameters
        data = request.get_json() or {}
        step_delay = data.get("step_delay", 2)
        proximity_threshold = data.get("proximity_threshold_km", 0.05)

        # Start simulation for the agent
        result = simulate_single_agent_movement(
            agent_id, step_delay, proximity_threshold
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/routes/dashboard", methods=["GET"])
def get_routes_dashboard():
    """Get comprehensive route tracking dashboard data"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        # Get enhanced live tracking data
        live_data = get_enhanced_live_tracking_data()

        # Get simulation status
        simulation_status = {
            "active": route_optimizer_active,
            "timestamp": datetime.now().isoformat(),
        }

        # Get routes summary
        routes_ref = db.reference("optimized_routes")
        all_routes = routes_ref.get() or {}

        routes_summary = {
            "total_optimized_routes": len(all_routes),
            "average_route_points": 0,
        }

        if all_routes:
            total_points = sum(len(route) for route in all_routes.values())
            routes_summary["average_route_points"] = total_points / len(all_routes)

        return jsonify(
            {
                "success": True,
                "dashboard": {
                    "live_tracking": live_data.get("live_tracking", []),
                    "simulation": simulation_status,
                    "routes_summary": routes_summary,
                    "active_agents": live_data.get("total_active_agents", 0),
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders", methods=["GET"])
def get_all_orders():
    """Get all orders from Firebase"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        orders_ref = db.reference("orders")
        orders = orders_ref.get() or {}

        # Convert to list format for frontend
        orders_list = []
        for order_id, order_data in orders.items():
            orders_list.append({
                "id": order_id,
                "order_id": order_data.get("order_id", order_id),
                "items": ", ".join(order_data.get("order_items", [])),
                "location": f"{order_data.get('delivery_location', {}).get('lat', 0):.3f}, {order_data.get('delivery_location', {}).get('lng', 0):.3f}",
                "status": order_data.get("current_status", "unknown"),
                "sla": order_data.get("sla", "N/A"),
                "delivered_at": order_data.get("delivered_at", None)
            })

        return jsonify({"success": True, "orders": orders_list})

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
        try:
            delivery_status_response = get_delivery_status()
            if isinstance(delivery_status_response, tuple):
                delivery_status = (
                    delivery_status_response[0].get_json()
                    if delivery_status_response[1] == 200
                    else {}
                )
            else:
                delivery_status = delivery_status_response.get_json() if hasattr(delivery_status_response, 'get_json') else {}
        except Exception as e:
            print(f"Error getting delivery status: {e}")
            delivery_status = {}

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

        response_data = {
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
        
        # Debug logging
        print(f"📊 Dashboard API Response:")
        print(f"  - Total orders: {orders_summary.get('total_orders', 0)}")
        print(f"  - Orders by status: {orders_summary.get('orders_by_status', {})}")
        print(f"  - Available agents: {len(delivery_manager.available_agents)}")
        print(f"  - Orders to assign: {len(delivery_manager.orders_to_assign)}")
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/test/add-order", methods=["POST"])
def add_test_order():
    """Add a test order to Firebase for testing the automated workflow"""
    try:
        if not firebase_initialized:
            return jsonify({"success": False, "error": "Firebase not initialized"}), 500

        data = request.get_json() or {}
        
        # Generate a unique order ID
        import random
        order_id = f"ORD{random.randint(1000, 9999)}"
        
        # Create test order
        test_order = {
            "order_id": order_id,
            "order_items": data.get("items", ["Test Item 1", "Test Item 2"]),
            "delivery_location": data.get("delivery_location", {
                "lat": 18.5204 + random.uniform(-0.01, 0.01),
                "lng": 73.8567 + random.uniform(-0.01, 0.01)
            }),
            "current_status": "unpicked",
            "customer_name": data.get("customer_name", "Test Customer"),
            "city": data.get("city", "Pune"),
            "state": data.get("state", "Maharashtra"),
            "pincode": data.get("pincode", "411001"),
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "order_time": datetime.now().strftime("%H:%M:%S"),
            "created_at": datetime.now().isoformat()
        }
        
        # Add to Firebase
        orders_ref = db.reference("orders")
        orders_ref.child(order_id).set(test_order)
        
        return jsonify({
            "success": True,
            "message": f"Test order {order_id} added successfully",
            "order_id": order_id,
            "order_data": test_order
        })
        
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
