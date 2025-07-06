import firebase_admin
from firebase_admin import db
import math
from datetime import datetime


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


class DeliveryManager:
    def _init_(self):
        # Initialize delivery agents from Firebase
        self.delivery_agents = []
        self.load_delivery_agents_from_firebase()

    def load_delivery_agents_from_firebase(self):
        """Load delivery agents from Firebase database"""
        try:
            if not firebase_admin._apps:
                print("Firebase not initialized, using empty delivery agents list")
                self.delivery_agents = []
                return

            # Get all delivery agents from Firebase
            ref = db.reference("delivery_agents")
            agents = ref.get()

            if not agents:
                print("No delivery agents found in Firebase")
                self.delivery_agents = []
                return

            self.delivery_agents = []
            for agent_key, agent_data in agents.items():
                # Convert Firebase data to our internal format
                agent = {
                    "id": agent_data.get("delivery_agent_id", agent_key),
                    "name": agent_data.get("delivery_agent_name", "Unknown"),
                    "active": False,  # Will be updated based on current assignments
                    "assigned_orders": [],  # Will be populated from orders
                    "vehicle_type": agent_data.get("vehicle_type", "bike"),
                    "current_location": {
                        "lat": agent_data.get("current_location", {}).get("lat", 0),
                        "lng": agent_data.get("current_location", {}).get("lng", 0),
                    },
                    "phone": agent_data.get("contact_number", ""),
                    "status": agent_data.get(
                        "status", "available"
                    ),  # available, busy, offline
                    "is_active": agent_data.get("is_active", True),
                    "rating": agent_data.get("rating", 0),
                    "shift_start_time": agent_data.get("shift_start_time", "09:00"),
                    "shift_end_time": agent_data.get("shift_end_time", "18:00"),
                    "zone": agent_data.get("zone", ""),
                    "total_orders_completed": agent_data.get(
                        "total_orders_completed", 0
                    ),
                    "created_at": agent_data.get("created_at", ""),
                    "last_updated": agent_data.get("last_updated", ""),
                }
                self.delivery_agents.append(agent)

            # Load current assignments from orders
            self.sync_assignments_from_orders()

            print(f"Loaded {len(self.delivery_agents)} delivery agents from Firebase")

        except Exception as e:
            print(f"Error loading delivery agents from Firebase: {e}")
            self.delivery_agents = []

    def sync_assignments_from_orders(self):
        """Sync delivery agent assignments from current orders"""
        try:
            if not firebase_admin._apps:
                return

            # Get all orders from Firebase
            orders_ref = db.reference("orders")
            orders = orders_ref.get()

            if not orders:
                return

            # Reset all assignments first
            for agent in self.delivery_agents:
                agent["assigned_orders"] = []
                agent["active"] = False

            # Update assignments based on orders
            for order_id, order_data in orders.items():
                delivery_status = order_data.get("delivery_status", "").lower()
                delivery_agent_id = order_data.get(
                    "delivery_boy_id"
                )  # Note: keeping original field name

                if delivery_status == "delivery_boy_assigned" and delivery_agent_id:
                    # Find the delivery agent
                    agent = next(
                        (
                            a
                            for a in self.delivery_agents
                            if a["id"] == delivery_agent_id
                        ),
                        None,
                    )
                    if agent:
                        agent["assigned_orders"].append(order_id)
                        agent["active"] = True
                        agent["status"] = "busy"

        except Exception as e:
            print(f"Error syncing assignments from orders: {e}")

    def refresh_delivery_agents(self):
        """Refresh delivery agents data from Firebase"""
        self.load_delivery_agents_from_firebase()

    def get_delivery_boys_status(self):
        """Get current status of all delivery agents"""
        # Refresh data from Firebase
        self.refresh_delivery_agents()

        available_agents = [
            agent
            for agent in self.delivery_agents
            if not agent["active"]
            and agent["status"] == "available"
            and agent["is_active"]
        ]

        active_agents = [agent for agent in self.delivery_agents if agent["active"]]

        offline_agents = [
            agent
            for agent in self.delivery_agents
            if agent["status"] == "offline" or not agent["is_active"]
        ]

        return {
            "success": True,
            "delivery_boys": self.delivery_agents,
            "total_boys": len(self.delivery_agents),
            "available_boys": len(available_agents),
            "active_boys": len(active_agents),
            "offline_boys": len(offline_agents),
        }

    def get_delivery_boy_assignments(self):
        """Get current delivery agent assignments"""
        self.refresh_delivery_agents()

        available_slots = len(
            [
                agent
                for agent in self.delivery_agents
                if not agent["active"]
                and agent["status"] == "available"
                and agent["is_active"]
            ]
        )

        return {
            "delivery_boys": self.delivery_agents,
            "active_count": len(
                [agent for agent in self.delivery_agents if agent["active"]]
            ),
            "available_slots": available_slots,
        }

    def get_picked_orders_from_firebase(self):
        """Get list of orders that are picked and ready for delivery"""
        try:
            if not firebase_admin._apps:
                return []

            # Get all orders from Firebase
            ref = db.reference("/orders")
            orders = ref.get()

            if not orders:
                return []

            picked_orders = []
            for order_key, order_data in orders.items():
                # Check if order status is 'picked' and not already assigned to delivery
                current_status = order_data.get("current_status", "").lower()
                delivery_status = order_data.get("delivery_status", "").lower()

                if (
                    current_status == "picked"
                    and delivery_status != "delivery_boy_assigned"
                ):
                    picked_orders.append(
                        {
                            "order_id": order_key,
                            "order_data": order_data,
                            "current_status": current_status,
                            "delivery_status": delivery_status,
                        }
                    )

            return picked_orders

        except Exception as e:
            print(f"Error fetching picked orders: {e}")
            return []

    def update_order_delivery_status_in_firebase(
        self, order_id, delivery_status, delivery_boy_id=None
    ):
        """Update order delivery status in Firebase"""
        try:
            if not firebase_admin._apps:
                print("Firebase not initialized, cannot update order delivery status")
                return False

            # Update the order delivery status in Firebase
            ref = db.reference(f"orders/{order_id}")
            order_data = ref.get()

            if order_data:
                # Update delivery_status and add timestamp
                updates = {
                    "delivery_status": delivery_status,
                    "delivery_last_updated": datetime.now().isoformat(),
                }

                # Add delivery boy assignment if provided
                if delivery_boy_id:
                    updates["delivery_boy_id"] = delivery_boy_id
                    updates["delivery_assigned_at"] = datetime.now().isoformat()

                # Add specific timestamps based on status
                if delivery_status.lower() == "out_for_delivery":
                    updates["out_for_delivery_at"] = datetime.now().isoformat()
                elif delivery_status.lower() == "delivered":
                    updates["delivered_at"] = datetime.now().isoformat()

                ref.update(updates)
                print(
                    f"Order {order_id} delivery status updated to '{delivery_status}' in Firebase"
                )
                return True
            else:
                print(f"Order {order_id} not found in Firebase")
                return False

        except Exception as e:
            print(f"Error updating order delivery status in Firebase: {e}")
            return False

    def assign_order_to_delivery_boy(self, order_id=None, delivery_boy_id=None):
        """Assign an order to an available delivery agent"""
        try:
            # Refresh delivery agents data
            self.refresh_delivery_agents()

            # Get all currently assigned orders to prevent duplicates
            currently_assigned_orders = []
            for agent in self.delivery_agents:
                if agent["active"]:
                    currently_assigned_orders.extend(agent["assigned_orders"])

            # If specific order_id provided, check if it's available
            if order_id:
                # Check if order is already assigned to someone
                if order_id in currently_assigned_orders:
                    assigned_agent = next(
                        (
                            agent
                            for agent in self.delivery_agents
                            if order_id in agent["assigned_orders"]
                        ),
                        None,
                    )
                    agent_name = assigned_agent["name"] if assigned_agent else "Unknown"
                    return {
                        "success": False,
                        "message": f"Order {order_id} is already assigned to {agent_name}",
                    }

                # Check if order exists and is picked in Firebase
                picked_orders = self.get_picked_orders_from_firebase()
                available_order_ids = [order["order_id"] for order in picked_orders]

                if order_id not in available_order_ids:
                    return {
                        "success": False,
                        "message": f"Order {order_id} is not available for delivery (not picked or already assigned)",
                    }
            else:
                # Get next available picked order that's not currently assigned
                picked_orders = self.get_picked_orders_from_firebase()
                available_orders = [
                    order
                    for order in picked_orders
                    if order["order_id"] not in currently_assigned_orders
                ]

                if not available_orders:
                    return {
                        "success": False,
                        "message": "No picked orders available for delivery assignment",
                    }

                # Get the first available order
                order_id = available_orders[0]["order_id"]

            # Find available delivery agent
            available_agent = None
            if delivery_boy_id:
                available_agent = next(
                    (
                        agent
                        for agent in self.delivery_agents
                        if agent["id"] == delivery_boy_id
                        and not agent["active"]
                        and agent["status"] == "available"
                        and agent["is_active"]
                    ),
                    None,
                )
                if not available_agent:
                    return {
                        "success": False,
                        "message": f"Delivery agent {delivery_boy_id} is not available or doesn't exist",
                    }
            else:
                available_agent = next(
                    (
                        agent
                        for agent in self.delivery_agents
                        if not agent["active"]
                        and agent["status"] == "available"
                        and agent["is_active"]
                    ),
                    None,
                )

            if not available_agent:
                return {"success": False, "message": "No available delivery agents"}

            # Double-check: Ensure this delivery agent is not already active
            if available_agent["active"]:
                return {
                    "success": False,
                    "message": f"Delivery agent {available_agent['name']} is already active",
                }

            # Update order delivery status to 'delivery_boy_assigned' in Firebase
            firebase_updated = self.update_order_delivery_status_in_firebase(
                order_id, "delivery_boy_assigned", available_agent["id"]
            )

            # Assign the order to delivery agent
            available_agent["active"] = True
            available_agent["assigned_orders"].append(order_id)
            available_agent["status"] = "busy"

            return {
                "success": True,
                "delivery_boy": available_agent,
                "firebase_updated": firebase_updated,
                "message": f"Order {order_id} assigned to {available_agent['name']}",
            }

        except Exception as e:
            print(f"Error in assign_order_to_delivery_boy: {e}")
            return {"success": False, "message": f"Assignment failed: {str(e)}"}

    def assign_orders_with_batching(self, max_distance_km=1.0):
        """Assign orders to delivery agents with intelligent batching"""
        try:
            # Refresh delivery agents data
            self.refresh_delivery_agents()

            # Use same error handling pattern as picking API
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}

            # Get orders with same error handling as picking API
            try:
                orders_ref = db.reference("orders")
                orders = orders_ref.get()

                if not orders:
                    return {
                        "success": True,
                        "assignments": [],
                        "total_orders_assigned": 0,
                        "message": "No orders found in Firebase",
                    }

            except Exception as firebase_error:
                print(f"Error fetching orders from Firebase: {firebase_error}")
                return {
                    "success": False,
                    "message": f"Firebase connection failed: {str(firebase_error)}",
                }

            # Rest of the existing code continues here...
            assigned_orders = set()
            assignment_results = []

            # First, get already assigned orders and update local state
            for order_id, order_data in orders.items():
                if order_data.get("delivery_status") == "delivery_boy_assigned":
                    assigned_orders.add(order_id)
                    # Update local delivery agents state
                    agent_id = order_data.get("delivery_boy_id")
                    if agent_id:
                        # Find delivery agent by ID
                        delivery_agent = next(
                            (
                                agent
                                for agent in self.delivery_agents
                                if agent["id"] == agent_id
                            ),
                            None,
                        )
                        if (
                            delivery_agent
                            and order_id not in delivery_agent["assigned_orders"]
                        ):
                            delivery_agent["assigned_orders"].append(order_id)
                            delivery_agent["active"] = True
                            delivery_agent["status"] = "busy"

            # Process unassigned orders
            for order_id, order_data in orders.items():
                if (
                    order_data.get("current_status") != "picked"
                ):  # Note: lowercase to match your requirement
                    continue
                if order_data.get("delivery_status") == "delivery_boy_assigned":
                    continue

                coords1 = order_data.get("delivery_location")
                if not coords1:
                    continue

                lat1 = coords1.get("lat")
                lng1 = coords1.get("lng")

                if lat1 is None or lng1 is None:
                    continue

                # Find available delivery agent
                selected_agent = None
                for agent in self.delivery_agents:
                    if (
                        not agent["active"]
                        and agent["status"] == "available"
                        and agent["is_active"]
                    ):
                        selected_agent = agent
                        break

                if not selected_agent:
                    continue

                # Assign primary order with error handling
                try:
                    orders_ref.child(order_id).update(
                        {
                            "delivery_boy_id": selected_agent["id"],
                            "delivery_status": "delivery_boy_assigned",
                            "delivery_assigned_at": datetime.now().isoformat(),
                        }
                    )
                except Exception as update_error:
                    print(f"Error updating order {order_id}: {update_error}")
                    continue

                selected_agent["assigned_orders"].append(order_id)
                selected_agent["active"] = True
                selected_agent["status"] = "busy"
                assigned_orders.add(order_id)

                primary_assignment = {
                    "order_id": order_id,
                    "delivery_boy_id": selected_agent["id"],
                    "delivery_boy_name": selected_agent["name"],
                    "delivery_boy_phone": selected_agent["phone"],
                    "delivery_boy_vehicle": selected_agent["vehicle_type"],
                    "delivery_boy_zone": selected_agent["zone"],
                    "type": "primary",
                    "batched_orders": [],
                }

                # Batch nearby orders
                for other_id, other_data in orders.items():
                    if other_id in assigned_orders or other_id == order_id:
                        continue
                    if other_data.get("current_status") != "picked":
                        continue
                    if other_data.get("delivery_status") == "delivery_boy_assigned":
                        continue

                    coords2 = other_data.get("delivery_location")
                    if not coords2:
                        continue

                    lat2 = coords2.get("lat")
                    lng2 = coords2.get("lng")

                    if lat2 is None or lng2 is None:
                        continue

                    distance = haversine(lat1, lng1, lat2, lng2)
                    if distance < max_distance_km:
                        # Batch this order with error handling
                        try:
                            orders_ref.child(other_id).update(
                                {
                                    "delivery_boy_id": selected_agent["id"],
                                    "delivery_status": "delivery_boy_assigned",
                                    "delivery_assigned_at": datetime.now().isoformat(),
                                    "batched_with": order_id,
                                    "distance_from_primary": round(distance, 2),
                                }
                            )
                        except Exception as batch_error:
                            print(f"Error batching order {other_id}: {batch_error}")
                            continue

                        selected_agent["assigned_orders"].append(other_id)
                        assigned_orders.add(other_id)

                        primary_assignment["batched_orders"].append(
                            {"order_id": other_id, "distance_km": round(distance, 2)}
                        )

                assignment_results.append(primary_assignment)

            return {
                "success": True,
                "assignments": assignment_results,
                "total_orders_assigned": len(assigned_orders),
                "delivery_boys_status": self.get_delivery_boys_status(),
                "message": f"Successfully assigned {len(assigned_orders)} orders to delivery agents",
            }

        except Exception as e:
            print(f"Error in assign_orders_with_batching: {e}")
            return {"success": False, "message": f"Assignment failed: {str(e)}"}

    def get_delivery_assignments(self):
        """Get detailed delivery assignments"""
        try:
            self.refresh_delivery_agents()

            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}

            orders_ref = db.reference("orders")
            orders = orders_ref.get() or {}

            detailed_assignments = {}

            for agent in self.delivery_agents:
                agent_orders = []
                for order_id in agent["assigned_orders"]:
                    if order_id in orders:
                        order_info = orders[order_id]
                        agent_orders.append(
                            {
                                "order_id": order_id,
                                "customer_name": order_info.get(
                                    "customer_name", "Unknown"
                                ),
                                "delivery_address": order_info.get(
                                    "delivery_address", "Unknown"
                                ),
                                "delivery_location": order_info.get(
                                    "delivery_location", {}
                                ),
                                "delivery_status": order_info.get(
                                    "delivery_status", "unknown"
                                ),
                                "total_amount": order_info.get("total_amount", 0),
                                "batched_with": order_info.get("batched_with"),
                                "distance_from_primary": order_info.get(
                                    "distance_from_primary"
                                ),
                            }
                        )

                detailed_assignments[f"agent_{agent['id']}"] = {
                    "delivery_agent": agent,
                    "orders": agent_orders,
                    "total_orders": len(agent_orders),
                }

            return {
                "success": True,
                "assignments": detailed_assignments,
                "summary": self.get_delivery_boys_status(),
            }

        except Exception as e:
            return {"success": False, "message": f"Failed to get assignments: {str(e)}"}

    def reset_delivery_assignments(self):
        """Reset all delivery assignments"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}

            orders_ref = db.reference("orders")
            orders = orders_ref.get() or {}

            # Reset Firebase orders
            for order_id, order_data in orders.items():
                if order_data.get("delivery_status") == "delivery_boy_assigned":
                    orders_ref.child(order_id).update(
                        {
                            "delivery_boy_id": None,
                            "delivery_status": "pending",
                            "delivery_assigned_at": None,
                            "batched_with": None,
                            "distance_from_primary": None,
                        }
                    )

            # Reset local delivery agents
            self.refresh_delivery_agents()

            return {
                "success": True,
                "message": "All delivery assignments reset",
                "delivery_boys_status": self.get_delivery_boys_status(),
            }

        except Exception as e:
            return {"success": False, "message": f"Reset failed: {str(e)}"}

    def update_delivery_status(self, order_id, status):
        """Update delivery status for a specific order"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}

            orders_ref = db.reference("orders")
            order_ref = orders_ref.child(order_id)
            order_data = order_ref.get()

            if not order_data:
                return {"success": False, "message": f"Order {order_id} not found"}

            # Update delivery status
            updates = {
                "delivery_status": status,
                "delivery_last_updated": datetime.now().isoformat(),
            }

            if status == "delivered":
                updates["delivered_at"] = datetime.now().isoformat()
                # Remove from delivery agent's assigned orders
                agent_id = order_data.get("delivery_boy_id")
                if agent_id:
                    delivery_agent = next(
                        (
                            agent
                            for agent in self.delivery_agents
                            if agent["id"] == agent_id
                        ),
                        None,
                    )
                    if delivery_agent and order_id in delivery_agent["assigned_orders"]:
                        delivery_agent["assigned_orders"].remove(order_id)
                        # If no more orders, make delivery agent available
                        if not delivery_agent["assigned_orders"]:
                            delivery_agent["active"] = False
                            delivery_agent["status"] = "available"

            elif status == "out_for_delivery":
                updates["out_for_delivery_at"] = datetime.now().isoformat()

            order_ref.update(updates)

            return {
                "success": True,
                "message": f"Order {order_id} delivery status updated to {status}",
                "order_id": order_id,
                "new_status": status,
            }

        except Exception as e:
            return {"success": False, "message": f"Status update failed: {str(e)}"}

    def get_next_available_order(self):
        """Get the next available order for delivery assignment"""
        try:
            self.refresh_delivery_agents()
            picked_orders = self.get_picked_orders_from_firebase()

            # Get orders that are currently assigned to delivery agents
            currently_assigned_orders = []
            for agent in self.delivery_agents:
                if agent["active"]:
                    currently_assigned_orders.extend(agent["assigned_orders"])

            # Filter out orders that are currently assigned
            available_orders = [
                order
                for order in picked_orders
                if order["order_id"] not in currently_assigned_orders
            ]

            # Get delivery agent statistics
            total_agents = len(self.delivery_agents)
            active_agents = len(
                [agent for agent in self.delivery_agents if agent["active"]]
            )
            available_agents = len(
                [
                    agent
                    for agent in self.delivery_agents
                    if not agent["active"]
                    and agent["status"] == "available"
                    and agent["is_active"]
                ]
            )

            return {
                "success": True,
                "available_orders": available_orders,
                "orders_in_queue": len(available_orders),
                "total_delivery_agents": total_agents,
                "active_delivery_agents": active_agents,
                "available_delivery_agents": available_agents,
                "can_assign_more": available_agents > 0 and len(available_orders) > 0,
                "queue_status": {
                    "orders_waiting": max(0, len(available_orders) - available_agents),
                    "next_assignable": min(len(available_orders), available_agents),
                },
            }

        except Exception as e:
            print(f"Error getting next available order: {e}")
            return {
                "success": False,
                "message": f"Failed to get available orders: {str(e)}",
            }

    def complete_delivery(self, delivery_boy_id, order_id):
        """Mark a specific order as delivered and handle auto-assignment"""
        try:
            delivery_agent = next(
                (
                    agent
                    for agent in self.delivery_agents
                    if agent["id"] == delivery_boy_id
                ),
                None,
            )
            if not delivery_agent or not delivery_agent["active"]:
                return {
                    "success": False,
                    "message": "Delivery agent not found or not active",
                }

            if order_id not in delivery_agent["assigned_orders"]:
                return {
                    "success": False,
                    "message": f"Order {order_id} is not assigned to this delivery agent",
                }

            # Update order status to 'delivered' in Firebase
            firebase_updated = self.update_order_delivery_status_in_firebase(
                order_id, "delivered"
            )

            # Remove the specific order from delivery agent's assigned orders
            delivery_agent["assigned_orders"].remove(order_id)

            # If no more orders, make delivery agent available
            if not delivery_agent["assigned_orders"]:
                delivery_agent["active"] = False
                delivery_agent["status"] = "available"

                # Check if there are more orders waiting for auto-assignment
                queue_status = self.get_next_available_order()
                auto_assignment = None

                if (
                    queue_status["success"]
                    and queue_status["orders_in_queue"] > 0
                    and queue_status["available_delivery_agents"] > 0
                ):
                    available_orders = queue_status["available_orders"]
                    if available_orders:
                        next_order_id = available_orders[0]["order_id"]
                        # Try to auto-assign the next order to this now-free delivery agent
                        auto_assignment = self.assign_order_to_delivery_boy(
                            order_id=next_order_id, delivery_boy_id=delivery_boy_id
                        )

                return {
                    "success": True,
                    "completed_order": order_id,
                    "delivery_agent": delivery_agent,
                    "firebase_updated": firebase_updated,
                    "auto_assignment": auto_assignment,
                    "message": f"Order {order_id} delivered by {delivery_agent['name']} and marked as 'delivered' in Firebase",
                }
            else:
                return {
                    "success": True,
                    "completed_order": order_id,
                    "delivery_agent": delivery_agent,
                    "firebase_updated": firebase_updated,
                    "message": f"Order {order_id} delivered by {delivery_agent['name']}. {len(delivery_agent['assigned_orders'])} orders remaining.",
                }

        except Exception as e:
            print(f"Error in complete_delivery: {e}")
            return {
                "success": False,
                "message": f"Delivery completion failed: {str(e)}",
            }

    def reset_all_delivery_boys(self):
        """Reset all delivery agent assignments and update Firebase statuses"""
        try:
            # Reset Firebase statuses for currently assigned orders
            for agent in self.delivery_agents:
                if agent["active"]:
                    for order_id in agent["assigned_orders"]:
                        # Reset order delivery status back to pending
                        self.update_order_delivery_status_in_firebase(
                            order_id, "pending"
                        )

            # Refresh delivery agents and reset assignments
            self.refresh_delivery_agents()

            return {
                "success": True,
                "message": "All delivery agents reset and Firebase statuses updated",
                "data": self.get_delivery_boys_status(),
            }

        except Exception as e:
            return {"success": False, "message": f"Reset failed: {str(e)}"}

    def get_delivery_agent_performance(self):
        """Get delivery agent performance metrics"""
        try:
            self.refresh_delivery_agents()

            performance_data = []
            for agent in self.delivery_agents:
                performance_data.append(
                    {
                        "agent_id": agent["id"],
                        "agent_name": agent["name"],
                        "total_orders_completed": agent["total_orders_completed"],
                        "rating": agent["rating"],
                        "current_orders": len(agent["assigned_orders"]),
                        "status": agent["status"],
                        "is_active": agent["is_active"],
                        "vehicle_type": agent["vehicle_type"],
                        "zone": agent["zone"],
                        "shift_start": agent["shift_start_time"],
                        "shift_end": agent["shift_end_time"],
                    }
                )

            return {
                "success": True,
                "performance_data": performance_data,
                "total_agents": len(self.delivery_agents),
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get performance data: {str(e)}",
            }
