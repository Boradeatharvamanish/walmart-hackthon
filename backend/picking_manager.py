import json
from datetime import datetime, timedelta
import threading
import time


class AdvancedPickingManager:
    def __init__(self):
        self.pickers = [
            {
                "id": 1,
                "name": "Alex Kumar",
                "active": False,
                "order_id": None,
                "progress": 0,
                "assigned_at": None,
                "estimated_completion": None,
                "items_picked": [],
                "current_location": "Counter",
            },
            {
                "id": 2,
                "name": "Priya Sharma",
                "active": False,
                "order_id": None,
                "progress": 0,
                "assigned_at": None,
                "estimated_completion": None,
                "items_picked": [],
                "current_location": "Counter",
            },
            {
                "id": 3,
                "name": "Raj Patel",
                "active": False,
                "order_id": None,
                "progress": 0,
                "assigned_at": None,
                "estimated_completion": None,
                "items_picked": [],
                "current_location": "Counter",
            },
            {
                "id": 4,
                "name": "Sarah Khan",
                "active": False,
                "order_id": None,
                "progress": 0,
                "assigned_at": None,
                "estimated_completion": None,
                "items_picked": [],
                "current_location": "Counter",
            },
            {
                "id": 5,
                "name": "Mike Johnson",
                "active": False,
                "order_id": None,
                "progress": 0,
                "assigned_at": None,
                "estimated_completion": None,
                "items_picked": [],
                "current_location": "Counter",
            },
        ]

        self.order_queue = []
        self.completed_orders = []
        self.picking_history = []

        # Store layout for optimal picking paths
        self.store_layout = {
            "Dairy": ["Milk", "Butter", "Eggs", "Paneer"],
            "Grocery": ["Bread", "Soap", "Juice"],
            "Fresh": ["Vegetables", "Fruits"],
            "Frozen": ["Ice Cream", "Frozen Foods"],
        }

        # Estimated time per item (in minutes)
        self.item_pick_times = {
            "Milk": 1,
            "Butter": 1,
            "Eggs": 2,
            "Paneer": 2,
            "Bread": 1,
            "Soap": 1,
            "Juice": 1,
            "Vegetables": 3,
            "Fruits": 3,
            "Ice Cream": 1,
            "Frozen Foods": 2,
        }

        self.lock = threading.Lock()

    def generate_optimal_path(self, items):
        """Generate optimal picking path based on store layout"""
        path = []
        sections_needed = []

        for item in items:
            for section, section_items in self.store_layout.items():
                if any(
                    section_item.lower() in item.lower()
                    for section_item in section_items
                ):
                    if section not in sections_needed:
                        sections_needed.append(section)
                    break

        # Optimal section order (minimize backtracking)
        optimal_order = ["Dairy", "Fresh", "Grocery", "Frozen"]
        ordered_sections = [
            section for section in optimal_order if section in sections_needed
        ]

        for section in ordered_sections:
            section_items = [
                item
                for item in items
                if any(
                    section_item.lower() in item.lower()
                    for section_item in self.store_layout[section]
                )
            ]
            path.extend([(section, item) for item in section_items])

        return path

    def estimate_picking_time(self, items):
        """Estimate total picking time for items"""
        total_time = 0
        for item in items:
            # Default time if item not in mapping
            base_time = 2
            for mapped_item, time_val in self.item_pick_times.items():
                if mapped_item.lower() in item.lower():
                    base_time = time_val
                    break
            total_time += base_time

        # Add base travel time between sections
        sections = set()
        for item in items:
            for section, section_items in self.store_layout.items():
                if any(
                    section_item.lower() in item.lower()
                    for section_item in section_items
                ):
                    sections.add(section)
                    break

        travel_time = len(sections) * 0.5  # 30 seconds between sections
        return total_time + travel_time

    def assign_order_to_best_picker(self, order_data):
        """Assign order to the best available picker"""
        with self.lock:
            available_pickers = [p for p in self.pickers if not p["active"]]

            if not available_pickers:
                return {
                    "success": False,
                    "message": "No available pickers - order added to queue",
                }

            # For now, just take the first available picker
            # Could implement more sophisticated assignment logic here
            picker = available_pickers[0]

            items = order_data.get("order_items", [])
            estimated_time = self.estimate_picking_time(items)
            optimal_path = self.generate_optimal_path(items)

            picker.update(
                {
                    "active": True,
                    "order_id": order_data.get("order_id"),
                    "progress": 0,
                    "assigned_at": datetime.now(),
                    "estimated_completion": datetime.now()
                    + timedelta(minutes=estimated_time),
                    "items_picked": [],
                    "current_location": "Counter",
                    "optimal_path": optimal_path,
                    "total_items": len(items),
                    "estimated_time": estimated_time,
                }
            )

            return {
                "success": True,
                "picker": picker,
                "estimated_time": estimated_time,
                "optimal_path": optimal_path,
            }

    def update_picker_location_and_progress(
        self, picker_id, location=None, item_picked=None
    ):
        """Update picker's current location and progress"""
        with self.lock:
            picker = next((p for p in self.pickers if p["id"] == picker_id), None)

            if not picker or not picker["active"]:
                return {"success": False, "message": "Picker not found or not active"}

            if location:
                picker["current_location"] = location

            if item_picked:
                if item_picked not in picker["items_picked"]:
                    picker["items_picked"].append(item_picked)
                    picker["progress"] = (
                        len(picker["items_picked"]) / picker["total_items"]
                    ) * 100

            return {"success": True, "picker": picker, "progress": picker["progress"]}

    def complete_order(self, picker_id):
        """Complete an order and free up the picker"""
        with self.lock:
            picker = next((p for p in self.pickers if p["id"] == picker_id), None)

            if not picker or not picker["active"]:
                return {"success": False, "message": "Picker not found or not active"}

            completed_order = {
                "order_id": picker["order_id"],
                "picker_id": picker_id,
                "picker_name": picker["name"],
                "completed_at": datetime.now(),
                "assigned_at": picker["assigned_at"],
                "actual_time": (datetime.now() - picker["assigned_at"]).total_seconds()
                / 60,
                "estimated_time": picker.get("estimated_time", 0),
                "items_picked": picker["items_picked"],
            }

            self.completed_orders.append(completed_order)
            self.picking_history.append(completed_order)

            # Reset picker
            picker.update(
                {
                    "active": False,
                    "order_id": None,
                    "progress": 0,
                    "assigned_at": None,
                    "estimated_completion": None,
                    "items_picked": [],
                    "current_location": "Counter",
                    "optimal_path": [],
                    "total_items": 0,
                    "estimated_time": 0,
                }
            )

            return {
                "success": True,
                "completed_order": completed_order,
                "picker": picker,
            }

    def get_dashboard_data(self):
        """Get comprehensive dashboard data"""
        with self.lock:
            active_picks = []
            for picker in self.pickers:
                if picker["active"]:
                    pick_data = picker.copy()
                    # Calculate time remaining
                    if pick_data["estimated_completion"]:
                        time_remaining = (
                            pick_data["estimated_completion"] - datetime.now()
                        ).total_seconds() / 60
                        pick_data["time_remaining"] = max(0, time_remaining)
                    else:
                        pick_data["time_remaining"] = 0

                    # Format datetime objects for JSON serialization
                    if pick_data["assigned_at"]:
                        pick_data["assigned_at"] = pick_data["assigned_at"].isoformat()
                    if pick_data["estimated_completion"]:
                        pick_data["estimated_completion"] = pick_data[
                            "estimated_completion"
                        ].isoformat()

                    active_picks.append(pick_data)

            return {
                "active_picks": active_picks,
                "available_pickers": len([p for p in self.pickers if not p["active"]]),
                "queue_length": len(self.order_queue),
                "completed_today": len(
                    [
                        order
                        for order in self.completed_orders
                        if order["completed_at"].date() == datetime.now().date()
                    ]
                ),
                "average_pick_time": self.calculate_average_pick_time(),
                "picker_efficiency": self.calculate_picker_efficiency(),
            }

    def calculate_average_pick_time(self):
        """Calculate average picking time from history"""
        if not self.picking_history:
            return 0

        recent_picks = self.picking_history[-20:]  # Last 20 picks
        total_time = sum(pick["actual_time"] for pick in recent_picks)
        return total_time / len(recent_picks)

    def calculate_picker_efficiency(self):
        """Calculate efficiency metrics for each picker"""
        efficiency = {}

        for picker in self.pickers:
            picker_history = [
                pick
                for pick in self.picking_history
                if pick["picker_id"] == picker["id"]
            ]

            if picker_history:
                avg_actual = sum(pick["actual_time"] for pick in picker_history) / len(
                    picker_history
                )
                avg_estimated = sum(
                    pick["estimated_time"] for pick in picker_history
                ) / len(picker_history)

                efficiency[picker["name"]] = {
                    "orders_completed": len(picker_history),
                    "avg_time": avg_actual,
                    "efficiency_ratio": (
                        avg_estimated / avg_actual if avg_actual > 0 else 0
                    ),
                    "on_time_percentage": len(
                        [
                            p
                            for p in picker_history
                            if p["actual_time"] <= p["estimated_time"] * 1.1
                        ]
                    )
                    / len(picker_history)
                    * 100,
                }
            else:
                efficiency[picker["name"]] = {
                    "orders_completed": 0,
                    "avg_time": 0,
                    "efficiency_ratio": 0,
                    "on_time_percentage": 0,
                }

        return efficiency
