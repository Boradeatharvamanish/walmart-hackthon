# delivery_manager.py
from sklearn.cluster import KMeans
import numpy as np
from firebase_admin import db
import time


class DeliveryManager:
    def _init_(self):
        self.available_agents = []
        self.orders_to_assign = []
        self._load_available_agents()
        self._load_picked_orders()

    def _load_available_agents(self):
        agents_ref = db.reference("delivery_agents")
        all_agents = agents_ref.get()

        for agent_id, agent_data in all_agents.items():
            if agent_data.get("status") == "available":
                agent_info = {
                    "id": agent_data.get("delivery_agent_id"),
                    "name": agent_data.get("delivery_agent_name"),
                    "status": agent_data.get("status"),
                    "total_orders": 0,
                    "assigned_orders": [],
                    "current_location": {
                        "lat": agent_data.get("current_location", {}).get("lat", 0),
                        "lng": agent_data.get("current_location", {}).get("lng", 0),
                    },
                }
                self.available_agents.append(agent_info)

    def _load_picked_orders(self):
        orders_ref = db.reference("orders")
        all_orders = orders_ref.get()

        for order_id, order_data in all_orders.items():
            if order_data.get("current_status") == "Picked":
                order_info = {
                    "order_id": order_data.get("order_id"),
                    "order_items": order_data.get("order_items", []),
                    "delivery_location": {
                        "lat": order_data.get("delivery_location", {}).get("lat", 0),
                        "lng": order_data.get("delivery_location", {}).get("lng", 0),
                    },
                    "pincode": order_data.get("pincode", ""),
                }
                self.orders_to_assign.append(order_info)

    def cluster_orders_by_location(self):
        if not self.orders_to_assign:
            print("No orders to cluster.")
            return

        if not self.available_agents:
            print("No available delivery agents to assign clusters.")
            return

        num_clusters = min(2, len(self.orders_to_assign))  # Only 2 clusters max

        coordinates = [
            [order["delivery_location"]["lat"], order["delivery_location"]["lng"]]
            for order in self.orders_to_assign
        ]

        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(coordinates)

        self.clusters = [{"cluster_id": i, "orders": []} for i in range(num_clusters)]

        for idx, label in enumerate(labels):
            order = self.orders_to_assign[idx]
            self.clusters[label]["orders"].append(
                {
                    "order_id": order["order_id"],
                    "delivery_location": order["delivery_location"],
                }
            )

        print(f"{num_clusters} clusters formed and stored in self.clusters.")

    def assign_clusters_to_agents(self):
        if not hasattr(self, "clusters") or not self.clusters:
            print("No clusters available to assign.")
            return

        for i, cluster in enumerate(self.clusters):
            if i >= len(self.available_agents):
                break  # Only assign as many clusters as agents available

            agent = self.available_agents[i]
            agent_id = agent["id"]
            order_ids = [order["order_id"] for order in cluster["orders"]]

            # Update delivery_agents
            agent_ref = db.reference(f"delivery_agents/{agent_id}")
            agent_ref.update({"order_assigned": order_ids, "status": "busy"})

            # Update each order
            for order_id in order_ids:
                order_ref = db.reference(f"orders/{order_id}")
                order_ref.update(
                    {
                        "current_status": "out for delivery",
                        "delivery_agent_assigned": agent_id,
                    }
                )

            agent["total_orders"] = len(order_ids)
            agent["assigned_orders"] = order_ids

        print("Clusters assigned to available agents.")

    def watch_and_assign(self, interval=60):
        print("[Watcher] Started monitoring for new orders and agent status updates...")

        while True:
            try:
                # 🔁 Refresh available agents and orders
                self.available_agents = []
                self.orders_to_assign = []
                self._load_available_agents()
                self._load_picked_orders()

                if self.orders_to_assign and self.available_agents:
                    print(
                        f"[Watcher] Found {len(self.orders_to_assign)} new picked orders."
                    )
                    self.cluster_orders_by_location()
                    self.assign_clusters_to_agents()
                else:
                    print(
                        "[Watcher] No new orders or no available agents at the moment."
                    )

                # Optional: Monitor and log current agent statuses
                agent_ref = db.reference("delivery_agents")
                all_agents = agent_ref.get()
                for agent_id, agent_data in all_agents.items():
                    print(
                        f"Agent {agent_id} - Status: {agent_data.get('status')}, Orders: {agent_data.get('order_assigned', [])}"
                    )

            except Exception as e:
                print(f"[Watcher] Error occurred: {str(e)}")

            time.sleep(interval)  # Wait before next cycle (default: 60 sec)
