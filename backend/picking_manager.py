import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import time
import threading


class PickingManager:
    def __init__(self):
        self.picker_ids = [1, 2, 3, 4, 5]
        self.default_pickers = [
            {
                "id": 1,
                "name": "Alex Kumar",
                "active": False,
                "order_id": None,
                "progress": 0,
                "order_details": {},
            },
            {
                "id": 2,
                "name": "Priya Sharma",
                "active": False,
                "order_id": None,
                "progress": 0,
                "order_details": {},
            },
            {
                "id": 3,
                "name": "Raj Patel",
                "active": False,
                "order_id": None,
                "progress": 0,
                "order_details": {},
            },
            {
                "id": 4,
                "name": "Sarah Khan",
                "active": False,
                "order_id": None,
                "progress": 0,
                "order_details": {},
            },
            {
                "id": 5,
                "name": "Mike Johnson",
                "active": False,
                "order_id": None,
                "progress": 0,
                "order_details": {},
            },
        ]
        self.pickers = self.load_pickers_from_firebase()
        self.auto_assign_enabled = True
        self.start_auto_assignment_monitor()

    def load_pickers_from_firebase(self):
        """Load pickers from Firebase, or initialize if not present"""
        try:
            if not firebase_admin._apps:
                print(
                    "[PickingManager] Firebase not initialized, using default pickers"
                )
                return [dict(p) for p in self.default_pickers]
                
            pickers_ref = db.reference("pickers")
            pickers_data = pickers_ref.get()
            
            if not pickers_data:
                # Initialize pickers in Firebase
                for picker in self.default_pickers:
                    pickers_ref.child(str(picker["id"])).set(picker)
                print("[PickingManager] ✅ Initialized pickers in Firebase")
                return [dict(p) for p in self.default_pickers]
            else:
                # Handle both dict and list formats from Firebase
                pickers_list = []
                
                if isinstance(pickers_data, list):
                    # If it's already a list, filter out None values
                    pickers_list = [p for p in pickers_data if p is not None]
                else:
                    # Convert dict to list
                    for pid in self.picker_ids:
                        picker = pickers_data.get(str(pid))
                        if picker is not None:
                            pickers_list.append(picker)
                        else:
                            # If missing, add default
                            default_picker = next(
                                (p for p in self.default_pickers if p["id"] == pid),
                                None,
                            )
                            if default_picker:
                                pickers_ref.child(str(pid)).set(default_picker)
                                pickers_list.append(default_picker)
                
                # Ensure all required fields exist for each picker
                for picker in pickers_list:
                    if picker is not None:
                        picker.setdefault("active", False)
                        picker.setdefault("order_id", None)
                        picker.setdefault("progress", 0)
                        picker.setdefault("order_details", {})
                
                print(
                    f"[PickingManager] ✅ Loaded {len(pickers_list)} pickers from Firebase"
                )
                return pickers_list
        except Exception as e:
            print(f"[PickingManager] ❌ Error loading pickers from Firebase: {e}")
            return [dict(p) for p in self.default_pickers]

    def save_picker_to_firebase(self, picker):
        """Save picker data to Firebase"""
        try:
            if not firebase_admin._apps:
                print("[PickingManager] Firebase not initialized, cannot save picker")
                return False
                
            pickers_ref = db.reference("pickers")
            pickers_ref.child(str(picker["id"])).set(picker)
            print(f"[PickingManager] ✅ Saved picker {picker['id']} to Firebase")
            return True
        except Exception as e:
            print(
                f"[PickingManager] ❌ Error saving picker {picker['id']} to Firebase: {e}"
            )
            return False

    def get_picker_assignments(self):
        """Get current picker assignments from Firebase"""
        try:
            if not firebase_admin._apps:
                return {
                    "pickers": self.pickers,
                    "active_count": len([p for p in self.pickers if p["active"]]),
                    "available_slots": len(
                        [p for p in self.pickers if not p["active"]]
                    ),
                }
                
            pickers_ref = db.reference("pickers")
            pickers_data = pickers_ref.get() or {}
            
            # Handle both dict and list formats from Firebase
            if isinstance(pickers_data, list):
                pickers_list = [p for p in pickers_data if p is not None]
            else:
                # Convert dict to list
                pickers_list = []
                for pid in self.picker_ids:
                    picker = pickers_data.get(str(pid), {})
                    if picker is not None:
                        pickers_list.append(picker)
                    else:
                        # Add default picker if missing
                        default_picker = next(
                            (p for p in self.default_pickers if p["id"] == pid),
                            None,
                        )
                        if default_picker:
                            pickers_list.append(default_picker)
            
            # Ensure all required fields exist for each picker
            valid_pickers = []
            for picker in pickers_list:
                if picker is not None:
                    picker.setdefault("active", False)
                    picker.setdefault("order_id", None)
                    picker.setdefault("progress", 0)
                    picker.setdefault("order_details", {})
                    valid_pickers.append(picker)
            
            # Attach order details to active pickers
            orders_ref = db.reference("orders")
            orders = orders_ref.get() or {}
            
            for picker in valid_pickers:
                if picker.get("active") and picker.get("order_id"):
                    order = orders.get(picker["order_id"])
                    picker["order_details"] = order if order else {}
            
            return {
                "pickers": valid_pickers,
                "active_count": len([p for p in valid_pickers if p.get("active")]),
                "available_slots": len(
                    [p for p in valid_pickers if not p.get("active")]
                ),
            }
        except Exception as e:
            print(f"[PickingManager] ❌ Error getting picker assignments: {e}")
            return {
                "pickers": self.pickers,
                "active_count": len([p for p in self.pickers if p["active"]]),
                "available_slots": len([p for p in self.pickers if not p["active"]]),
            }

    def get_unpicked_orders_from_firebase(self):
        """Get all unpicked orders from Firebase"""
        try:
            if not firebase_admin._apps:
                print("[PickingManager] Firebase not initialized, cannot fetch orders")
                return []
                
            ref = db.reference("orders")
            orders = ref.get()
            if not orders:
                return []
                
            unpicked_orders = []
            for order_key, order_data in orders.items():
                if order_data is not None:
                    current_status = order_data.get("current_status", "").lower()
                    if current_status in ["unpicked", "pending", ""]:
                        unpicked_orders.append(
                            {
                                "order_id": order_key,
                                "order_data": order_data,
                                "current_status": current_status,
                            }
                        )
            
            print(f"[PickingManager] 📦 Found {len(unpicked_orders)} unpicked orders")
            return unpicked_orders
        except Exception as e:
            print(f"[PickingManager] ❌ Error fetching unpicked orders: {e}")
            return []

    def update_order_status_in_firebase(self, order_id, status):
        """Update order status in Firebase"""
        try:
            if not firebase_admin._apps:
                print(
                    "[PickingManager] Firebase not initialized, cannot update order status"
                )
                return False
                
            ref = db.reference(f"orders/{order_id}")
            order_data = ref.get()
            if order_data:
                updates = {
                    "current_status": status,
                    "last_updated": datetime.now().isoformat(),
                }
                if status.lower() == "picked":
                    updates["picked_at"] = datetime.now().isoformat()
                    updates["picked_by"] = "picking_system"
                elif status.lower() == "picking":
                    updates["picking_started_at"] = datetime.now().isoformat()
                    
                ref.update(updates)
                print(
                    f"[PickingManager] ✅ Order {order_id} status updated to '{status}' in Firebase"
                )
                return True
            else:
                print(f"[PickingManager] ❌ Order {order_id} not found in Firebase")
                return False
        except Exception as e:
            print(f"[PickingManager] ❌ Error updating order status in Firebase: {e}")
            return False

    def assign_order_to_picker(self, order_id=None, picker_id=None):
        """Assign an order to a picker"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}
                
            pickers_ref = db.reference("pickers")
            pickers_data = pickers_ref.get() or {}
            
            # Handle both dict and list formats from Firebase
            if isinstance(pickers_data, list):
                pickers_list = [p for p in pickers_data if p is not None]
            else:
                # Convert dict to list
                pickers_list = []
                for pid in self.picker_ids:
                    picker = pickers_data.get(str(pid), {})
                    if picker is not None:
                        pickers_list.append(picker)
            
            # Ensure all required fields exist for each picker
            valid_pickers = []
            for picker in pickers_list:
                if picker is not None:
                    picker.setdefault("active", False)
                    picker.setdefault("order_id", None)
                    picker.setdefault("progress", 0)
                    valid_pickers.append(picker)
            
            # Get all currently assigned orders
            currently_assigned_orders = [
                p.get("order_id")
                for p in valid_pickers
                if p.get("active") and p.get("order_id")
            ]
            
            # If specific order_id provided, check if it's available
            if order_id:
                if order_id in currently_assigned_orders:
                    picker_name = next(
                        (
                            p.get("name")
                            for p in valid_pickers
                            if p.get("order_id") == order_id
                        ),
                        "Unknown",
                    )
                    return {
                        "success": False,
                        "message": f"Order {order_id} is already assigned to {picker_name}",
                    }
                    
                unpicked_orders = self.get_unpicked_orders_from_firebase()
                available_order_ids = [order["order_id"] for order in unpicked_orders]
                if order_id not in available_order_ids:
                    return {
                        "success": False,
                        "message": f"Order {order_id} is not available for picking",
                    }
            else:
                # Get next available order
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
                order_id = available_orders[0]["order_id"]
            
            # Find available picker
            available_picker = None
            if picker_id:
                picker_data = next(
                    (p for p in valid_pickers if p.get("id") == picker_id), None
                )
                if picker_data and not picker_data.get("active"):
                    available_picker = picker_data
            else:
                # Find first available picker
                for picker in valid_pickers:
                    if not picker.get("active"):
                        available_picker = picker
                        break
            
            if not available_picker:
                return {"success": False, "message": "No available pickers"}
            
            if available_picker.get("active"):
                return {
                    "success": False,
                    "message": f"Picker {available_picker.get('name')} is already active",
                }
            
            # Update order status to 'picking' in Firebase
            firebase_updated = self.update_order_status_in_firebase(order_id, "picking")
            
            # Assign the order to picker
            available_picker["active"] = True
            available_picker["order_id"] = order_id
            available_picker["progress"] = 0
            
            # Get order details
            orders_ref = db.reference("orders")
            order_data = orders_ref.child(order_id).get()
            available_picker["order_details"] = order_data if order_data else {}
            
            # Save to Firebase
            self.save_picker_to_firebase(available_picker)
            
            return {
                "success": True,
                "picker": available_picker,
                "firebase_updated": firebase_updated,
                "message": f"Order {order_id} assigned to {available_picker['name']}",
            }
        except Exception as e:
            print(f"[PickingManager] ❌ Error in assign_order_to_picker: {e}")
            return {"success": False, "message": f"Assignment failed: {str(e)}"}

    def update_picker_progress(self, picker_id, progress):
        """Update picker progress"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}
                
            pickers_ref = db.reference("pickers")
            picker = pickers_ref.child(str(picker_id)).get()
            
            if picker and picker.get("active"):
                picker["progress"] = min(100, max(0, progress))
                self.save_picker_to_firebase(picker)
                
                # Auto-complete if progress reaches 100%
                if picker["progress"] >= 100:
                    return self.complete_picking(picker_id)
                
                return {"success": True, "picker": picker}
            
            return {"success": False, "message": "Picker not found or not active"}
        except Exception as e:
            print(f"[PickingManager] ❌ Error updating picker progress: {e}")
            return {"success": False, "message": f"Progress update failed: {str(e)}"}

    def complete_picking(self, picker_id):
        """Complete picking for a picker and update Firebase"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}
                
            pickers_ref = db.reference("pickers")
            picker = pickers_ref.child(str(picker_id)).get()
            
            if not picker or not picker.get("active"):
                return {"success": False, "message": "Picker not found or not active"}
            
            completed_order = picker["order_id"]
            
            # Update order status to 'picked' in Firebase
            firebase_updated = self.update_order_status_in_firebase(
                completed_order, "picked"
            )
            
            # Free up the picker
            picker["active"] = False
            picker["order_id"] = None
            picker["progress"] = 0
            picker["order_details"] = {}
            
            # Save to Firebase
            self.save_picker_to_firebase(picker)
            
            print(
                f"[PickingManager] ✅ Order {completed_order} completed by {picker['name']}"
            )
            
            return {
                "success": True,
                "completed_order": completed_order,
                "picker": picker,
                "firebase_updated": firebase_updated,
                "message": f"Order {completed_order} completed by {picker['name']} and marked as 'picked'",
            }
        except Exception as e:
            print(f"[PickingManager] ❌ Error in complete_picking: {e}")
            return {"success": False, "message": f"Completion failed: {str(e)}"}

    def get_next_available_order(self):
        """Get the next available order for picking with queue management"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}
                
            unpicked_orders = self.get_unpicked_orders_from_firebase()
            
            # Get orders that are currently being picked
            pickers_ref = db.reference("pickers")
            pickers_data = pickers_ref.get() or {}
            
            # Handle both dict and list formats from Firebase
            if isinstance(pickers_data, list):
                pickers_list = [p for p in pickers_data if p is not None]
            else:
                # Convert dict to list
                pickers_list = []
                for pid in self.picker_ids:
                    picker = pickers_data.get(str(pid), {})
                    if picker is not None:
                        pickers_list.append(picker)
            
            # Filter out None values and ensure all pickers have required fields
            valid_pickers = []
            for picker in pickers_list:
                if picker is not None:
                    picker.setdefault("active", False)
                    picker.setdefault("order_id", None)
                    picker.setdefault("progress", 0)
                    valid_pickers.append(picker)
            
            currently_assigned_orders = [
                p.get("order_id")
                for p in valid_pickers
                if p.get("active") and p.get("order_id")
            ]
            
            # Filter out orders that are currently being picked
            available_orders = [
                order
                for order in unpicked_orders
                if order["order_id"] not in currently_assigned_orders
            ]
            
            # Get picker statistics
            total_pickers = len(self.picker_ids)
            active_pickers = len([p for p in valid_pickers if p.get("active")])
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
            print(f"[PickingManager] ❌ Error getting next available order: {e}")
            return {
                "success": False,
                "message": f"Failed to get available orders: {str(e)}",
            }

    def auto_assign_orders(self):
        """Automatically assign available orders to available pickers"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}
                
            # Get current status
            status = self.get_next_available_order()
            if not status["success"]:
                return status
            
            available_orders = status["available_orders"]
            available_pickers = status["available_pickers"]
            
            if available_pickers == 0:
                return {
                    "success": False,
                    "message": "No available pickers for assignment",
                    "status": status,
                }
            
            if len(available_orders) == 0:
                return {
                    "success": False,
                    "message": "No orders available for assignment",
                    "status": status,
                }
            
            # Determine how many orders to assign
            orders_to_assign = min(len(available_orders), available_pickers)
            
            assignments = []
            failed_assignments = []
            
            # Assign orders one by one
            for i in range(orders_to_assign):
                order_id = available_orders[i]["order_id"]
                result = self.assign_order_to_picker(order_id)
                
                if result["success"]:
                    assignments.append(result)
                else:
                    failed_assignments.append(
                        {"order_id": order_id, "error": result["message"]}
                    )
            
            # Get updated status
            final_status = self.get_next_available_order()
            
            print(
                f"[PickingManager] ✅ Auto-assigned {len(assignments)} orders to pickers"
            )
            
            return {
                "success": True,
                "assignments": assignments,
                "failed_assignments": failed_assignments,
                "assigned_count": len(assignments),
                "failed_count": len(failed_assignments),
                "final_status": final_status,
                "message": f"Successfully assigned {len(assignments)} orders to pickers",
            }
        except Exception as e:
            print(f"[PickingManager] ❌ Error in auto_assign_orders: {e}")
            return {"success": False, "message": f"Auto-assignment failed: {str(e)}"}

    def reset_all_pickers(self):
        """Reset all picker assignments and update Firebase statuses"""
        try:
            if not firebase_admin._apps:
                return {"success": False, "message": "Firebase not initialized"}
                
            pickers_ref = db.reference("pickers")
            
            # Reset all pickers to default state
            for picker in self.default_pickers:
                pickers_ref.child(str(picker["id"])).set(picker)
            
            print("[PickingManager] ✅ All pickers reset successfully")
            
            return {
                "success": True,
                "message": "All pickers reset and Firebase statuses updated",
                "data": self.get_picker_assignments(),
            }
        except Exception as e:
            print(f"[PickingManager] ❌ Error in reset_all_pickers: {e}")
            return {"success": False, "message": f"Reset failed: {str(e)}"}

    def start_auto_assignment_monitor(self):
        """Start background thread to monitor and auto-assign orders"""
        def monitor_thread():
            print("[PickingManager] 🔄 Starting auto-assignment monitor...")
            while self.auto_assign_enabled:
                try:
                    if firebase_admin._apps:
                        # Check for available orders and pickers
                        status = self.get_next_available_order()
                        if status["success"] and status["can_assign_more"]:
                            print(f"[PickingManager] 🔄 Auto-assigning orders...")
                            self.auto_assign_orders()
                except Exception as e:
                    print(f"[PickingManager] ❌ Error in auto-assignment monitor: {e}")
                
                time.sleep(10)  # Check every 10 seconds
        
        monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
        monitor_thread.start()
        print("[PickingManager] ✅ Auto-assignment monitor started")

    def stop_auto_assignment_monitor(self):
        """Stop the auto-assignment monitor"""
        self.auto_assign_enabled = False
        print("[PickingManager] 🛑 Auto-assignment monitor stopped")
