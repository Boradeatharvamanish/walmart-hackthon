from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin - UPDATE THESE WITH YOUR CREDENTIALS
try:
    # Option 1: Using service account key file
    # cred = credentials.Certificate("path/to/your/serviceAccountKey.json")

    # Option 2: Using environment variable (recommended for production)
    # Make sure to set GOOGLE_APPLICATION_CREDENTIALS environment variable
    cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://your-database-url-default-rtdb.firebaseio.com/"  # Update this URL
        },
    )
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    print("Firebase features will be disabled")


class PickingManager:
    def __init__(self):
        self.pickers = [
            {
                "id": 1,
                "name": "Alex Kumar",
                "active": False,
                "order_id": None,
                "progress": 0,
            },
            {
                "id": 2,
                "name": "Priya Sharma",
                "active": False,
                "order_id": None,
                "progress": 0,
            },
            {
                "id": 3,
                "name": "Raj Patel",
                "active": False,
                "order_id": None,
                "progress": 0,
            },
            {
                "id": 4,
                "name": "Sarah Khan",
                "active": False,
                "order_id": None,
                "progress": 0,
            },
            {
                "id": 5,
                "name": "Mike Johnson",
                "active": False,
                "order_id": None,
                "progress": 0,
            },
        ]

    def get_picker_assignments(self):
        """Get current picker assignments"""
        return {
            "pickers": self.pickers,
            "active_count": len([p for p in self.pickers if p["active"]]),
            "available_slots": len([p for p in self.pickers if not p["active"]]),
        }

    def get_unpicked_orders_from_firebase(self):
        """Get list of orders that are not yet picked from Firebase"""
        try:
            if not firebase_admin._apps:
                return []

            # Get all orders from Firebase
            ref = db.reference("orders")
            orders = ref.get()

            if not orders:
                return []

            unpicked_orders = []
            for order_key, order_data in orders.items():
                # Check if order status is not 'picked' - but include 'picking' status orders
                # because we need to filter them out separately in the assignment logic
                current_status = order_data.get("current_status", "").lower()
                if current_status != "picked":
                    unpicked_orders.append(
                        {
                            "order_id": order_key,
                            "order_data": order_data,
                            "current_status": current_status,
                        }
                    )

            return unpicked_orders

        except Exception as e:
            print(f"Error fetching unpicked orders: {e}")
            return []

    def update_order_status_in_firebase(self, order_id, status):
        """Update order status in Firebase"""
        try:
            if not firebase_admin._apps:
                print("Firebase not initialized, cannot update order status")
                return False

            # Update the order status in Firebase
            ref = db.reference(f"orders/{order_id}")
            order_data = ref.get()

            if order_data:
                # Update current_status and add timestamp
                updates = {
                    "current_status": status,
                    "last_updated": datetime.now().isoformat(),
                }

                # Add picking completion timestamp if status is 'picked'
                if status.lower() == "picked":
                    updates["picked_at"] = datetime.now().isoformat()
                elif status.lower() == "picking":
                    updates["picking_started_at"] = datetime.now().isoformat()

                ref.update(updates)
                print(f"Order {order_id} status updated to '{status}' in Firebase")
                return True
            else:
                print(f"Order {order_id} not found in Firebase")
                return False

        except Exception as e:
            print(f"Error updating order status in Firebase: {e}")
            return False

    def assign_order_to_picker(self, order_id=None, picker_id=None):
        """Assign an order to an available picker with strict one-to-one mapping"""
        try:
            # Get all currently assigned orders to prevent duplicates
            currently_assigned_orders = [
                p["order_id"] for p in self.pickers if p["active"] and p["order_id"]
            ]

            # If specific order_id provided, check if it's available
            if order_id:
                # Check if order is already assigned to someone
                if order_id in currently_assigned_orders:
                    picker_name = next(
                        (p["name"] for p in self.pickers if p["order_id"] == order_id),
                        "Unknown",
                    )
                    return {
                        "success": False,
                        "message": f"Order {order_id} is already assigned to {picker_name}",
                    }

                # Check if order exists and is unpicked in Firebase
                unpicked_orders = self.get_unpicked_orders_from_firebase()
                available_order_ids = [order["order_id"] for order in unpicked_orders]

                if order_id not in available_order_ids:
                    return {
                        "success": False,
                        "message": f"Order {order_id} is not available for picking (already picked or doesn't exist)",
                    }
            else:
                # Get next available unpicked order that's not currently assigned
                unpicked_orders = self.get_unpicked_orders_from_firebase()
                available_orders = [
                    order
                    for order in unpicked_orders
                    if order["order_id"] not in currently_assigned_orders
                ]

                if not available_orders:
                    return {
                        "success": False,
                        "message": "No unpicked orders available for assignment",
                    }

                # Get the first available order
                order_id = available_orders[0]["order_id"]

            # Find available picker
            available_picker = None
            if picker_id:
                available_picker = next(
                    (
                        p
                        for p in self.pickers
                        if p["id"] == picker_id and not p["active"]
                    ),
                    None,
                )
                if not available_picker:
                    return {
                        "success": False,
                        "message": f"Picker {picker_id} is not available or doesn't exist",
                    }
            else:
                available_picker = next(
                    (p for p in self.pickers if not p["active"]), None
                )

            if not available_picker:
                return {"success": False, "message": "No available pickers"}

            # Double-check: Ensure this picker is not already active (safety check)
            if available_picker["active"]:
                return {
                    "success": False,
                    "message": f"Picker {available_picker['name']} is already active",
                }

            # Update order status to 'picking' in Firebase
            firebase_updated = self.update_order_status_in_firebase(order_id, "picking")

            # Assign the order to picker
            available_picker["active"] = True
            available_picker["order_id"] = order_id
            available_picker["progress"] = 0

            return {
                "success": True,
                "picker": available_picker,
                "firebase_updated": firebase_updated,
                "message": f"Order {order_id} assigned to {available_picker['name']}",
            }

        except Exception as e:
            print(f"Error in assign_order_to_picker: {e}")
            return {"success": False, "message": f"Assignment failed: {str(e)}"}

    def update_picker_progress(self, picker_id, progress):
        """Update picker progress"""
        picker = next((p for p in self.pickers if p["id"] == picker_id), None)
        if picker and picker["active"]:
            picker["progress"] = min(100, max(0, progress))
            return {"success": True, "picker": picker}
        return {"success": False, "message": "Picker not found or not active"}

    def complete_picking(self, picker_id):
        """Complete picking for a picker and update Firebase status to 'picked'"""
        try:
            picker = next((p for p in self.pickers if p["id"] == picker_id), None)
            if not picker or not picker["active"]:
                return {"success": False, "message": "Picker not found or not active"}

            completed_order = picker["order_id"]

            # Update order status to 'picked' in Firebase
            firebase_updated = self.update_order_status_in_firebase(
                completed_order, "picked"
            )

            # Free up the picker FIRST before checking for auto-assignment
            picker["active"] = False
            picker["order_id"] = None
            picker["progress"] = 0

            # NOW check if there are more orders waiting (after freeing up the picker)
            queue_status = self.get_next_available_order()
            auto_assignment = None

            if (
                queue_status["success"]
                and queue_status["orders_in_queue"] > 0
                and queue_status["available_pickers"] > 0
            ):
                # Get orders that are truly available (not being picked by anyone)
                available_orders = queue_status["available_orders"]
                if available_orders:
                    # Double-check: Get FRESH list of currently assigned orders after freeing up this picker
                    currently_assigned_orders = [
                        p["order_id"]
                        for p in self.pickers
                        if p["active"] and p["order_id"]
                    ]

                    # Find first order that is NOT currently assigned to any active picker
                    next_order_id = None
                    for order in available_orders:
                        if order["order_id"] not in currently_assigned_orders:
                            next_order_id = order["order_id"]
                            break

                    if next_order_id:
                        # Try to auto-assign the truly available order to this now-free picker
                        auto_assignment = self.assign_order_to_picker(
                            order_id=next_order_id, picker_id=picker_id
                        )

            return {
                "success": True,
                "completed_order": completed_order,
                "picker": picker,
                "firebase_updated": firebase_updated,
                "auto_assignment": auto_assignment,
                "message": f"Order {completed_order} completed by {picker['name']} and marked as 'picked' in Firebase",
            }

        except Exception as e:
            print(f"Error in complete_picking: {e}")
            return {"success": False, "message": f"Completion failed: {str(e)}"}

    def get_next_available_order(self):
        """Get the next available order for picking with queue management"""
        try:
            unpicked_orders = self.get_unpicked_orders_from_firebase()

            # Get orders that are currently being picked
            currently_assigned_orders = [
                p["order_id"] for p in self.pickers if p["active"] and p["order_id"]
            ]

            # Filter out orders that are currently being picked
            available_orders = [
                order
                for order in unpicked_orders
                if order["order_id"] not in currently_assigned_orders
            ]

            # Get picker statistics
            total_pickers = len(self.pickers)
            active_pickers = len([p for p in self.pickers if p["active"]])
            available_pickers = total_pickers - active_pickers

            return {
                "success": True,
                "available_orders": available_orders,
                "orders_in_queue": len(available_orders),
                "total_pickers": total_pickers,
                "active_pickers": active_pickers,
                "available_pickers": available_pickers,
                "can_assign_more": available_pickers > 0 and len(available_orders) > 0,
                "queue_status": {
                    "orders_waiting": max(0, len(available_orders) - available_pickers),
                    "next_assignable": min(len(available_orders), available_pickers),
                },
            }

        except Exception as e:
            print(f"Error getting next available order: {e}")
            return {
                "success": False,
                "message": f"Failed to get available orders: {str(e)}",
            }


# Global picking manager instance
picking_manager = PickingManager()


@app.route("/")
def home():
    return "Flask backend is running with Picking Management and Firebase integration."


@app.route("/api/picking/status", methods=["GET"])
def get_picking_status():
    """Get current picking status"""
    try:
        return jsonify(
            {"success": True, "data": picking_manager.get_picker_assignments()}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/available-orders", methods=["GET"])
def get_available_orders():
    """Get list of available orders for picking"""
    try:
        result = picking_manager.get_next_available_order()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/assign", methods=["POST"])
def assign_order():
    """Assign an order to a picker"""
    try:
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
    """Reset all picker assignments and update Firebase statuses"""
    try:
        # Reset Firebase statuses for currently picked orders
        for picker in picking_manager.pickers:
            if picker["active"] and picker["order_id"]:
                # Reset order status back to previous state (you might want to customize this)
                picking_manager.update_order_status_in_firebase(
                    picker["order_id"], "pending"
                )

            picker["active"] = False
            picker["order_id"] = None
            picker["progress"] = 0

        return jsonify(
            {
                "success": True,
                "message": "All pickers reset and Firebase statuses updated",
                "data": picking_manager.get_picker_assignments(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders/update-status", methods=["POST"])
def update_order_status():
    """Update order status in Firebase"""
    try:
        data = request.get_json()
        order_id = data.get("order_id")
        status = data.get("status")

        if not order_id or not status:
            return (
                jsonify(
                    {"success": False, "error": "order_id and status are required"}
                ),
                400,
            )

        # Update Firebase
        firebase_updated = picking_manager.update_order_status_in_firebase(
            order_id, status
        )

        return jsonify(
            {
                "success": True,
                "firebase_updated": firebase_updated,
                "message": f"Order {order_id} status updated to {status}",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("Starting Flask application...")
    print("Make sure to update Firebase configuration before running in production!")
    app.run(debug=True, port=5000)
