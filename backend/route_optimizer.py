import threading
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import requests
import polyline
from math import radians, sin, cos, sqrt, atan2

GOOGLE_MAPS_API_KEY = "AIzaSyAt_4b9l-VqtR0nL41tvZQupckKt8xb2I8"
DARK_STORE_LOCATION = {"lat": 18.5286, "lng": 73.8748}

# Global variables for simulation control
route_optimizer_active = False
simulation_thread = None
simulation_lock = threading.Lock()


def generate_tsp_route(origin, waypoints):
    """Fixed version of TSP route generation with proper error handling"""
    if not origin or not waypoints:
        return []

    # Remove duplicates and invalid waypoints
    valid_waypoints = []
    for wp in waypoints:
        if wp and "lat" in wp and "lng" in wp:
            valid_waypoints.append(wp)

    if not valid_waypoints:
        return []

    waypoints_str = "|".join([f"{wp['lat']},{wp['lng']}" for wp in valid_waypoints])

    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={origin['lat']},{origin['lng']}&"
        f"destination={valid_waypoints[-1]['lat']},{valid_waypoints[-1]['lng']}&"
        f"waypoints=optimize:true|{waypoints_str}&"
        f"key={GOOGLE_MAPS_API_KEY}&"
        f"departure_time=now&"
        f"traffic_model=best_guess"
    )

    try:
        response = requests.get(url)
        data = response.json()

        if "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]
            poly = route["overview_polyline"]["points"]
            decoded_points = polyline.decode(poly)  # Returns list of (lat, lng) tuples

            # Convert to list of lists for JSON serialization and frontend compatibility
            route_points = [[point[0], point[1]] for point in decoded_points]

            return route_points
        else:
            print(f"Failed to get route: {data.get('error_message', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Error generating route: {str(e)}")
        return []


def generate_optimized_routes_for_busy_agents():
    """Generate optimized routes for all busy agents"""
    agents_ref = db.reference("delivery_agents")
    agents_data = agents_ref.get()

    if not agents_data:
        print("[Route Generation] No agents found")
        return {}

    optimized_routes = {}
    print(f"[Route Generation] Processing {len(agents_data)} agents")

    for agent_id, agent_data in agents_data.items():
        if agent_data.get("status") != "busy":
            print(f"[Route Generation] Agent {agent_id} is not busy, skipping")
            continue

        assigned_orders = agent_data.get("order_assigned", [])
        if not assigned_orders:
            print(f"[Route Generation] Agent {agent_id} has no assigned orders")
            continue

        delivery_locations = []
        for order_id in assigned_orders:
            order = db.reference(f"orders/{order_id}").get()
            if order and "delivery_location" in order:
                delivery_locations.append(order["delivery_location"])

        if not delivery_locations:
            print(f"[Route Generation] Agent {agent_id} has no valid delivery locations")
            continue

        origin = agent_data.get("current_location", DARK_STORE_LOCATION)
        print(f"[Route Generation] Generating route for agent {agent_id} with {len(delivery_locations)} delivery locations")
        
        route_points = generate_tsp_route(origin, delivery_locations)

        if route_points:  # Only store if route was generated successfully
            optimized_routes[agent_id] = route_points
            print(f"[Route Generation] Successfully generated route for agent {agent_id} with {len(route_points)} points")
        else:
            print(f"[Route Generation] Failed to generate route for agent {agent_id}")

    print(f"[Route Generation] Generated routes for {len(optimized_routes)} agents")
    return optimized_routes


def reroute_if_traffic(agent_id, old_route_points, delay_threshold_minutes=5):
    """Enhanced rerouting with better traffic detection"""
    agent_ref = db.reference(f"delivery_agents/{agent_id}")
    agent_data = agent_ref.get()

    if not agent_data or agent_data.get("status") != "busy":
        print(f"[Reroute] Agent {agent_id} is not busy or missing.")
        return old_route_points

    assigned_orders = agent_data.get("order_assigned", [])
    if not assigned_orders:
        return old_route_points

    delivery_locations = []
    for order_id in assigned_orders:
        order_data = db.reference(f"orders/{order_id}").get()
        if order_data and "delivery_location" in order_data:
            delivery_locations.append(order_data["delivery_location"])

    if not delivery_locations:
        return old_route_points

    origin = agent_data.get("current_location", DARK_STORE_LOCATION)
    waypoints_str = "|".join(
        [f"{loc['lat']},{loc['lng']}" for loc in delivery_locations]
    )

    # Traffic-aware Google Maps Directions API call
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={origin['lat']},{origin['lng']}&"
        f"destination={delivery_locations[-1]['lat']},{delivery_locations[-1]['lng']}&"
        f"waypoints=optimize:true|{waypoints_str}&"
        f"departure_time=now&traffic_model=best_guess&key={GOOGLE_MAPS_API_KEY}"
    )

    try:
        response = requests.get(url)
        data = response.json()

        if "routes" not in data or not data["routes"]:
            print(f"[Reroute] Failed to fetch route for agent {agent_id}.")
            return old_route_points

        route_info = data["routes"][0]

        # Check if traffic data is available
        legs = route_info.get("legs", [])
        if not legs:
            return old_route_points

        total_duration_in_traffic = 0
        total_duration_without_traffic = 0

        for leg in legs:
            if "duration_in_traffic" in leg:
                total_duration_in_traffic += leg["duration_in_traffic"]["value"]
            total_duration_without_traffic += leg["duration"]["value"]

        delay_minutes = (
            total_duration_in_traffic - total_duration_without_traffic
        ) / 60.0

        if delay_minutes > delay_threshold_minutes:
            print(
                f"[Reroute] Detected traffic for agent {agent_id}. Delay: {delay_minutes:.1f} min. Rerouting..."
            )
            # Convert polyline to proper format
            decoded_points = polyline.decode(route_info["overview_polyline"]["points"])
            return [[point[0], point[1]] for point in decoded_points]
        else:
            print(
                f"[Reroute] No major delay for agent {agent_id}. Continue on original route."
            )
            return old_route_points

    except Exception as e:
        print(f"[Reroute] Error rerouting agent {agent_id}: {str(e)}")
        return old_route_points


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points"""
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # km


def calculate_route_progress(current_location, route_points):
    """Calculate how much of the route has been completed"""
    if not route_points or not current_location:
        return 0

    try:
        # Find the closest point on the route to current location
        min_distance = float("inf")
        closest_index = 0

        for i, point in enumerate(route_points):
            distance = haversine_distance(
                current_location["lat"], current_location["lng"], point[0], point[1]
            )
            if distance < min_distance:
                min_distance = distance
                closest_index = i

        # Calculate progress as percentage
        progress = (closest_index / len(route_points)) * 100
        return round(progress, 2)
    except:
        return 0


def simulate_single_agent_movement(agent_id, step_delay=3, proximity_threshold_km=0.05):
    """Simulate movement for a single agent along their route"""
    try:
        agent_ref = db.reference(f"delivery_agents/{agent_id}")
        agent_data = agent_ref.get()

        if not agent_data or agent_data.get("status") != "busy":
            return {"success": False, "message": "Agent not busy"}

        # Get route points
        route_ref = db.reference(f"optimized_routes/{agent_id}")
        route_points = route_ref.get()

        if not route_points:
            return {"success": False, "message": "No route found"}

        # Get delivery locations
        assigned_orders = agent_data.get("order_assigned", [])
        delivery_locations = []

        for order_id in assigned_orders:
            order = db.reference(f"orders/{order_id}").get()
            if order and "delivery_location" in order:
                delivery_locations.append(
                    {
                        "order_id": order_id,
                        "lat": order["delivery_location"]["lat"],
                        "lng": order["delivery_location"]["lng"],
                        "delivered": order.get("current_status") == "delivered",
                    }
                )

        print(f"[Simulation] Agent {agent_id} starting movement with {len(route_points)} route points")
        
        # Move along route
        for i, point in enumerate(route_points):
            if not route_optimizer_active:
                print(f"[Simulation] Stopping agent {agent_id} movement")
                break

            # Update agent location
            new_location = {"lat": point[0], "lng": point[1]}
            agent_ref.child("current_location").set(new_location)
            
            print(f"[Simulation] Agent {agent_id} moved to position {i+1}/{len(route_points)}: {new_location}")

            # Check for deliveries
            for loc in delivery_locations:
                if not loc["delivered"]:
                    distance = haversine_distance(
                        point[0], point[1], loc["lat"], loc["lng"]
                    )

                    if distance < proximity_threshold_km:
                        # Mark order as delivered
                        order_ref = db.reference(f"orders/{loc['order_id']}")
                        order_ref.child("current_status").set("delivered")
                        order_ref.child("delivered_at").set(
                            datetime.now().isoformat()
                        )

                        loc["delivered"] = True
                        print(
                            f"[Delivery] Order {loc['order_id']} delivered by Agent {agent_id} at distance {distance:.3f}km"
                        )

            # Add delay for realistic movement (longer for better visibility)
            time.sleep(step_delay)

        # Check if all deliveries are completed
        all_delivered = all(loc["delivered"] for loc in delivery_locations)
        if all_delivered:
            # Return agent to dark store
            agent_ref.update(
                {
                    "status": "available",
                    "order_assigned": [],
                    "current_location": DARK_STORE_LOCATION,
                }
            )

            # Remove from optimized routes
            route_ref.delete()

            print(f"[Complete] Agent {agent_id} completed all deliveries and returned to darkstore")

        return {"success": True, "message": "Movement simulation completed"}

    except Exception as e:
        print(f"[Error] Simulating agent {agent_id}: {str(e)}")
        return {"success": False, "error": str(e)}


def simulate_all_agents_movement(step_delay=3, proximity_threshold_km=0.05):
    """Simulate movement for all busy agents"""
    agents_ref = db.reference("delivery_agents")
    agents_data = agents_ref.get()

    if not agents_data:
        print("[Simulation] No agents found for movement simulation")
        return

    print(f"[Simulation] Starting movement simulation for {len(agents_data)} agents")
    
    # Create threads for each agent to simulate concurrent movement
    agent_threads = []

    for agent_id, agent_data in agents_data.items():
        if agent_data.get("status") != "busy":
            print(f"[Simulation] Agent {agent_id} is not busy, skipping")
            continue

        print(f"[Simulation] Creating movement thread for agent {agent_id}")
        
        # Create thread for each agent
        thread = threading.Thread(
            target=simulate_single_agent_movement,
            args=(agent_id, step_delay, proximity_threshold_km),
            daemon=True,
        )
        agent_threads.append(thread)
        thread.start()

    print(f"[Simulation] Started {len(agent_threads)} agent movement threads")
    
    # Wait for all agent simulations to complete
    for thread in agent_threads:
        thread.join()

    print("[Simulation] All agent movement simulations completed")


def start_route_simulation():
    """Start the route simulation in a separate thread"""
    global route_optimizer_active, simulation_thread

    with simulation_lock:
        if route_optimizer_active:
            return {"success": False, "message": "Simulation already running"}

        route_optimizer_active = True
        simulation_thread = threading.Thread(
            target=continuous_simulation_loop, daemon=True
        )
        simulation_thread.start()

        return {"success": True, "message": "Route simulation started"}


def stop_route_simulation():
    """Stop the route simulation"""
    global route_optimizer_active

    with simulation_lock:
        route_optimizer_active = False

    return {"success": True, "message": "Route simulation stopped"}


def continuous_simulation_loop():
    """Continuous simulation loop that runs in background"""
    global route_optimizer_active

    print("[Simulation] Starting continuous simulation loop")
    
    while route_optimizer_active:
        try:
            print("[Simulation] Starting simulation cycle...")
            
            # Generate routes for all busy agents
            optimized_routes = generate_optimized_routes_for_busy_agents()

            if optimized_routes:
                # Store routes in Firebase
                routes_ref = db.reference("optimized_routes")
                routes_ref.update(optimized_routes)

                print(f"[Simulation] Updated routes for {len(optimized_routes)} agents")
                print(f"[Simulation] Route data: {optimized_routes}")

                # Simulate movement for all agents with longer delays for visibility
                simulate_all_agents_movement(step_delay=3, proximity_threshold_km=0.05)
            else:
                print("[Simulation] No routes to update")

            # Check for traffic and reroute if needed
            agents_ref = db.reference("delivery_agents")
            agents_data = agents_ref.get() or {}

            for agent_id, agent_data in agents_data.items():
                if agent_data.get("status") == "busy":
                    routes_ref = db.reference(f"optimized_routes/{agent_id}")
                    old_route = routes_ref.get()

                    if old_route:
                        new_route = reroute_if_traffic(
                            agent_id, old_route, delay_threshold_minutes=5
                        )
                        if new_route != old_route:
                            routes_ref.set(new_route)
                            print(f"[Reroute] Agent {agent_id} rerouted due to traffic")

            # Sleep before next iteration (longer for better visibility)
            print("[Simulation] Simulation cycle completed, waiting 10 seconds...")
            time.sleep(10)  # Update every 10 seconds for better visibility

        except Exception as e:
            print(f"[Simulation Error] {str(e)}")
            time.sleep(10)

    print("[Simulation] Simulation loop stopped")


def get_enhanced_live_tracking_data():
    """Enhanced live tracking with proper route visualization data"""
    try:
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
                                "status": order.get("current_status", "pending"),
                                "customer_name": order.get("customer_name", "Unknown"),
                                "estimated_delivery_time": order.get(
                                    "estimated_delivery_time", ""
                                ),
                            }
                        )

                # Calculate progress along route
                current_location = agent_data.get(
                    "current_location", DARK_STORE_LOCATION
                )
                route_progress = calculate_route_progress(current_location, agent_route)

                tracking_info = {
                    "agent_id": agent_data.get("delivery_agent_id", agent_id),
                    "agent_name": agent_data.get(
                        "delivery_agent_name", f"Agent {agent_id}"
                    ),
                    "current_location": current_location,
                    "status": agent_data.get("status"),
                    "route_points": agent_route,  # [[lat, lng], [lat, lng], ...]
                    "delivery_locations": delivery_locations,
                    "assigned_orders": assigned_orders,
                    "total_deliveries": len(assigned_orders),
                    "completed_deliveries": len(
                        [d for d in delivery_locations if d["status"] == "delivered"]
                    ),
                    "route_progress": route_progress,  # Percentage of route completed
                    "last_updated": datetime.now().isoformat(),
                }

                live_tracking_data.append(tracking_info)

        return {
            "success": True,
            "live_tracking": live_tracking_data,
            "total_active_agents": len(live_tracking_data),
            "simulation_active": route_optimizer_active,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
