# delivery_manager.py
from sklearn.cluster import KMeans
import numpy as np
from firebase_admin import db
import time
from datetime import datetime


class DeliveryManager:
    def __init__(self):
        self.available_agents = []
        self.orders_to_assign = []
        self.clusters = []
        self._load_available_agents()
        self._load_picked_orders()

    def _load_available_agents(self):
        """Load available delivery agents from Firebase"""
        try:
            agents_ref = db.reference("delivery_agents")
            all_agents = agents_ref.get() or {}

            self.available_agents = []
            for agent_id, agent_data in all_agents.items():
                if agent_data.get("status") == "available":
                    agent_info = {
                        "id": agent_id,
                        "name": agent_data.get("delivery_agent_name", f"Agent {agent_id}"),
                        "status": agent_data.get("status"),
                        "total_orders": 0,
                        "assigned_orders": [],
                        "current_location": agent_data.get("current_location", {}),
                        "vehicle_type": agent_data.get("vehicle_type", "bike"),
                        "zone": agent_data.get("zone", "Unknown"),
                    }
                    self.available_agents.append(agent_info)
            
            print(f"[Delivery Manager] Loaded {len(self.available_agents)} available agents")
        except Exception as e:
            print(f"[Delivery Manager] Error loading agents: {e}")

    def _load_picked_orders(self):
        """Load picked orders from Firebase"""
        try:
            orders_ref = db.reference("orders")
            all_orders = orders_ref.get() or {}

            self.orders_to_assign = []
            for order_id, order_data in all_orders.items():
                # Check for both "Picked" and "picked" status (case insensitive)
                current_status = order_data.get("current_status", "").lower()
                if current_status == "picked" and not order_data.get("delivery_agent_assigned"):
                    order_info = {
                        "order_id": order_id,
                        "order_items": order_data.get("order_items", []),
                        "delivery_location": order_data.get("delivery_location", {}),
                        "pincode": order_data.get("pincode", ""),
                        "customer_name": order_data.get("customer_name", "Unknown"),
                        "city": order_data.get("city", ""),
                        "state": order_data.get("state", ""),
                    }
                    self.orders_to_assign.append(order_info)
            
            print(f"[Delivery Manager] Loaded {len(self.orders_to_assign)} picked orders")
        except Exception as e:
            print(f"[Delivery Manager] Error loading orders: {e}")

    def cluster_orders_by_location(self):
        """Cluster orders by delivery location"""
        if not self.orders_to_assign:
            print("[Delivery Manager] No orders to cluster.")
            return False

        if not self.available_agents:
            print("[Delivery Manager] No available delivery agents to assign clusters.")
            return False

        try:
            # Filter orders with valid delivery locations
            valid_orders = [
                order for order in self.orders_to_assign 
                if order["delivery_location"] and 
                order["delivery_location"].get("lat") and 
                order["delivery_location"].get("lng")
            ]

            if not valid_orders:
                print("[Delivery Manager] No orders with valid delivery locations.")
                return False

            coordinates = [
                [order["delivery_location"]["lat"], order["delivery_location"]["lng"]]
                for order in valid_orders
            ]

            # Determine number of clusters (max 1 cluster per available agent)
            num_clusters = min(len(self.available_agents), len(valid_orders))
            
            if num_clusters == 0:
                print("[Delivery Manager] No clusters to create.")
                return False

            # If only 1 cluster needed, don't use KMeans
            if num_clusters == 1:
                self.clusters = [{"cluster_id": 0, "orders": valid_orders}]
            else:
                kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init="auto")
                labels = kmeans.fit_predict(coordinates)

                self.clusters = [{"cluster_id": i, "orders": []} for i in range(num_clusters)]

                for idx, label in enumerate(labels):
                    order = valid_orders[idx]
                    self.clusters[label]["orders"].append(order)

            print(f"[Delivery Manager] Created {len(self.clusters)} clusters with {len(valid_orders)} orders")
            return True

        except Exception as e:
            print(f"[Delivery Manager] Error clustering orders: {e}")
            return False

    def assign_clusters_to_agents(self):
        """Assign clusters to available delivery agents"""
        if not hasattr(self, "clusters") or not self.clusters:
            print("[Delivery Manager] No clusters available to assign.")
            return False

        try:
            assigned_count = 0
            for i, cluster in enumerate(self.clusters):
                if i >= len(self.available_agents):
                    break  # Only assign as many clusters as agents available

                agent = self.available_agents[i]
                agent_id = agent["id"]
                order_ids = [order["order_id"] for order in cluster["orders"]]

                print(f"[Delivery Manager] Assigning cluster {i} with {len(order_ids)} orders to agent {agent_id}")

                # Update delivery_agents in Firebase
                agent_ref = db.reference(f"delivery_agents/{agent_id}")
                agent_ref.update({
                    "order_assigned": order_ids, 
                    "status": "busy",
                    "last_updated": datetime.now().isoformat()
                })

                # Update each order status
                for order_id in order_ids:
                    order_ref = db.reference(f"orders/{order_id}")
                    order_ref.update({
                        "current_status": "out for delivery",
                        "delivery_agent_assigned": agent_id,
                        "assigned_at": datetime.now().isoformat()
                    })

                assigned_count += 1

            print(f"[Delivery Manager] Successfully assigned {assigned_count} clusters to agents")
            return True

        except Exception as e:
            print(f"[Delivery Manager] Error assigning clusters: {e}")
            return False

    def watch_and_assign(self, interval=30):
        """Monitor and automatically assign picked orders to delivery agents"""
        print("[Delivery Manager] Started monitoring for picked orders and agent assignments...")

        while True:
            try:
                # 🔁 Refresh available agents and orders
                self._load_available_agents()
                self._load_picked_orders()

                if self.orders_to_assign and self.available_agents:
                    print(f"[Delivery Manager] Found {len(self.orders_to_assign)} picked orders and {len(self.available_agents)} available agents")
                    
                    # Create clusters and assign to agents
                    if self.cluster_orders_by_location():
                        self.assign_clusters_to_agents()
                else:
                    if not self.orders_to_assign:
                        print("[Delivery Manager] No picked orders available for delivery")
                    if not self.available_agents:
                        print("[Delivery Manager] No available delivery agents")

                # Log current agent statuses
                self._log_agent_statuses()

            except Exception as e:
                print(f"[Delivery Manager] Error in watch loop: {str(e)}")

            time.sleep(interval)  # Wait before next cycle

    def _log_agent_statuses(self):
        """Log current delivery agent statuses"""
        try:
            agent_ref = db.reference("delivery_agents")
            all_agents = agent_ref.get() or {}
            
            for agent_id, agent_data in all_agents.items():
                status = agent_data.get('status', 'unknown')
                orders = agent_data.get('order_assigned', [])
                print(f"Agent {agent_id} - Status: {status}, Orders: {orders}")
                
        except Exception as e:
            print(f"[Delivery Manager] Error logging agent statuses: {e}")

    def get_delivery_status(self):
        """Get current delivery status for API"""
        try:
            self._load_available_agents()
            self._load_picked_orders()
            
            return {
                "success": True,
                "available_agents": len(self.available_agents),
                "picked_orders": len(self.orders_to_assign),
                "can_assign": len(self.orders_to_assign) > 0 and len(self.available_agents) > 0
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
