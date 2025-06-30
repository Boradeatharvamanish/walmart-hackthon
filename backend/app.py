from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin (you'll need to add your service account key)
# Uncomment and configure these lines with your Firebase credentials
# cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
# firebase_admin.initialize_app(cred, {
#     'databaseURL': 'https://your-database-url.firebaseio.com/'
# })


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

    def assign_order_to_picker(self, order_id, picker_id=None):
        """Assign an order to an available picker"""
        # Find available picker
        available_picker = None
        if picker_id:
            available_picker = next(
                (p for p in self.pickers if p["id"] == picker_id and not p["active"]),
                None,
            )
        else:
            available_picker = next((p for p in self.pickers if not p["active"]), None)

        if available_picker:
            available_picker["active"] = True
            available_picker["order_id"] = order_id
            available_picker["progress"] = 0
            return {
                "success": True,
                "picker": available_picker,
                "message": f"Order {order_id} assigned to {available_picker['name']}",
            }

        return {"success": False, "message": "No available pickers"}

    def update_picker_progress(self, picker_id, progress):
        """Update picker progress"""
        picker = next((p for p in self.pickers if p["id"] == picker_id), None)
        if picker and picker["active"]:
            picker["progress"] = min(100, max(0, progress))
            return {"success": True, "picker": picker}
        return {"success": False, "message": "Picker not found or not active"}

    def complete_picking(self, picker_id):
        """Complete picking for a picker and free them up"""
        picker = next((p for p in self.pickers if p["id"] == picker_id), None)
        if picker and picker["active"]:
            completed_order = picker["order_id"]
            picker["active"] = False
            picker["order_id"] = None
            picker["progress"] = 0

            return {
                "success": True,
                "completed_order": completed_order,
                "picker": picker,
                "message": f"Order {completed_order} completed by {picker['name']}",
            }

        return {"success": False, "message": "Picker not found or not active"}


# Global picking manager instance
picking_manager = PickingManager()


@app.route("/")
def home():
    return "Flask backend is running with Picking Management."


@app.route("/api/picking/status", methods=["GET"])
def get_picking_status():
    """Get current picking status"""
    try:
        return jsonify(
            {"success": True, "data": picking_manager.get_picker_assignments()}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/picking/assign", methods=["POST"])
def assign_order():
    """Assign an order to a picker"""
    try:
        data = request.get_json()
        order_id = data.get("order_id")
        picker_id = data.get("picker_id")  # Optional

        if not order_id:
            return jsonify({"success": False, "error": "order_id is required"}), 400

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
    """Complete picking for a picker"""
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


@app.route("/api/picking/reset", methods=["POST"])
def reset_picking():
    """Reset all picker assignments (for testing)"""
    try:
        for picker in picking_manager.pickers:
            picker["active"] = False
            picker["order_id"] = None
            picker["progress"] = 0

        return jsonify(
            {
                "success": True,
                "message": "All pickers reset",
                "data": picking_manager.get_picker_assignments(),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders/update-status", methods=["POST"])
def update_order_status():
    """Update order status (integrate with Firebase if needed)"""
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

        # Here you would update Firebase
        # ref = db.reference(f'orders/{order_key}/current_status')
        # ref.set(status)

        return jsonify(
            {"success": True, "message": f"Order {order_id} status updated to {status}"}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
