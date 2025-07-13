import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:5000"
API_ENDPOINTS = {
    "health": "/health",
    "live_tracking": "/api/routes/live-tracking-enhanced",
    "generate_simulate": "/api/routes/generate-and-simulate",
    "simulation_status": "/api/routes/simulation/status",
    "simulation_start": "/api/routes/simulation/start",
    "simulation_stop": "/api/routes/simulation/stop",
}


def test_health():
    """Test if the backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False


def test_live_tracking():
    """Test live tracking data"""
    try:
        response = requests.get(f"{BASE_URL}{API_ENDPOINTS['live_tracking']}")
        data = response.json()

        if data.get("success"):
            print("✅ Live tracking API working")
            print(f"   Active agents: {data.get('total_active_agents', 0)}")
            if "debug" in data:
                print(f"   Debug info: {data['debug']}")
            return True
        else:
            print(f"❌ Live tracking failed: {data.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Live tracking error: {e}")
        return False


def test_route_generation():
    """Test route generation and simulation"""
    try:
        print("🔄 Testing route generation and simulation...")
        response = requests.post(f"{BASE_URL}{API_ENDPOINTS['generate_simulate']}")
        data = response.json()

        if data.get("success"):
            print("✅ Route generation successful")
            print(f"   Routes generated: {data.get('routes_count', 0)}")
            print(f"   Simulation started: {data.get('simulation_started', False)}")
            if "routes" in data:
                print(f"   Route data: {list(data['routes'].keys())}")
            return True
        else:
            print(
                f"❌ Route generation failed: {data.get('error', data.get('message', 'Unknown error'))}"
            )
            return False
    except Exception as e:
        print(f"❌ Route generation error: {e}")
        return False


def test_simulation_status():
    """Test simulation status"""
    try:
        response = requests.get(f"{BASE_URL}{API_ENDPOINTS['simulation_status']}")
        data = response.json()

        if data.get("success"):
            status = data.get("simulation_active", False)
            print(f"✅ Simulation status: {'Active' if status else 'Inactive'}")
            return status
        else:
            print(
                f"❌ Simulation status check failed: {data.get('error', 'Unknown error')}"
            )
            return False
    except Exception as e:
        print(f"❌ Simulation status error: {e}")
        return False


def test_simulation_control():
    """Test simulation start/stop"""
    try:
        # Start simulation
        print("🔄 Starting simulation...")
        response = requests.post(f"{BASE_URL}{API_ENDPOINTS['simulation_start']}")
        data = response.json()

        if data.get("success"):
            print("✅ Simulation started successfully")

            # Wait a bit
            time.sleep(2)

            # Check status
            if test_simulation_status():
                # Stop simulation
                print("🔄 Stopping simulation...")
                response = requests.post(
                    f"{BASE_URL}{API_ENDPOINTS['simulation_stop']}"
                )
                data = response.json()

                if data.get("success"):
                    print("✅ Simulation stopped successfully")
                    return True
                else:
                    print(
                        f"❌ Failed to stop simulation: {data.get('error', 'Unknown error')}"
                    )
                    return False
            else:
                print("❌ Simulation not active after start")
                return False
        else:
            print(
                f"❌ Failed to start simulation: {data.get('error', 'Unknown error')}"
            )
            return False
    except Exception as e:
        print(f"❌ Simulation control error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Route Optimization and Simulation System")
    print("=" * 50)

    # Test 1: Health check
    if not test_health():
        print("\n❌ Backend is not running. Please start the Flask server first.")
        return

    print("\n" + "=" * 50)

    # Test 2: Live tracking
    test_live_tracking()

    print("\n" + "=" * 50)

    # Test 3: Route generation
    test_route_generation()

    print("\n" + "=" * 50)

    # Test 4: Simulation status
    test_simulation_status()

    print("\n" + "=" * 50)

    # Test 5: Simulation control
    test_simulation_control()

    print("\n" + "=" * 50)
    print("🎉 Testing complete!")
    print("\n📋 Next steps:")
    print("1. Open the frontend in your browser")
    print("2. Go to the 'Live Tracking' tab")
    print("3. Click 'Generate & Simulate Routes' button")
    print("4. Watch the agents move along their routes on the map")


if __name__ == "__main__":
    main()
