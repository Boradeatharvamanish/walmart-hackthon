// tracking-dashboard-enhanced.js
// Live Tracking Dashboard with Enhanced Route Visualization

// API Configuration
// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:5000',
    ENDPOINTS: {
        LIVE_TRACKING: '/api/routes/live-tracking',
        DASHBOARD: '/api/routes/dashboard',
        REROUTE: '/api/routes/reroute',
        GENERATE_ALL: '/api/routes/generate-all',
        SIMULATION_START: '/api/routes/simulation/start',
        SIMULATION_STOP: '/api/routes/simulation/stop',
        SIMULATION_STATUS: '/api/routes/simulation/status',
        // NEW ENDPOINTS ADDED
        ENHANCED_LIVE_TRACKING: '/api/routes/live-tracking-enhanced', // Use this for all tracking updates
        GENERATE_AND_SIMULATE: '/api/routes/generate-and-simulate',
        SIMULATE_AGENT_MOVEMENT: '/api/routes/agent/<agent_id>/simulate' // Note: This needs dynamic agent_id
    }
};

// Helper function to build full URL
function buildApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}

class TrackingDashboard {
    constructor() {
        this.map = null;
        this.markers = {};
        this.polylines = {}; // For simple routes or to clear directionsRenderer
        this.infoWindows = {};
        this.directionsService = null;
        this.directionsRenderer = {}; // Store DirectionsRenderer instances per agent
        this.realTimeInterval = null;
        this.isRealTimeActive = false;
        this.isSimulationActive = false; // New property to track simulation status
        this.simulationInterval = null; // New property for the simulation interval
        this.darkstoreLocation = { lat: 18.5286, lng: 73.8748 }; // Default Pune location
        this.agentData = [];
        this.deliveryLocations = []; // Consolidated delivery locations
        this.routeColors = ['#FF5722', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', '#795548', '#607D8B'];
        this.animatedPaths = {}; // Stores the animated polyline for each agent
        this.pathAnimations = {}; // Stores the animation state for each agent
        this.animationSteps = {}; // Stores the current step for each agent's animation

        // Initialize when map is ready
        this.initializeTracking();
    }

    // Initialize tracking system
    initializeTracking() {
        // Wait for map to be initialized
        if (typeof google !== 'undefined' && google.maps) {
            this.initMap();
        } else {
            console.log('Waiting for Google Maps to load...');
            setTimeout(() => this.initializeTracking(), 1000);
        }
    }

    // Initialize Google Map
    initMap() {
        console.log('Initializing Google Maps...');
        
        const mapOptions = {
            zoom: 12,
            center: this.darkstoreLocation,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            styles: [
                {
                    "featureType": "all",
                    "elementType": "geometry.fill",
                    "stylers": [{ "color": "#1a1a1a" }]
                },
                {
                    "featureType": "all",
                    "elementType": "labels.text.fill",
                    "stylers": [{ "color": "#ffffff" }]
                },
                {
                    "featureType": "road",
                    "elementType": "geometry",
                    "stylers": [{ "color": "#2c2c2c" }]
                },
                {
                    "featureType": "water",
                    "elementType": "geometry",
                    "stylers": [{ "color": "#0f0f0f" }]
                }
            ]
        };

        const mapElement = document.getElementById('tracking-map');
        if (!mapElement) {
            console.error('Map element not found! Make sure you have a div with id="tracking-map"');
            return;
        }

        this.map = new google.maps.Map(mapElement, mapOptions);
        this.directionsService = new google.maps.DirectionsService();
        console.log('Google Maps initialized successfully');

        // Add darkstore marker
        this.addDarkstoreMarker();

        // Load initial data
        this.loadInitialTrackingData();

        // Set up event listeners
        this.setupEventListeners();

        // Check simulation status on startup
        this.checkSimulationStatus();
    }

    // Add darkstore marker
    addDarkstoreMarker() {
        const darkstoreMarker = new google.maps.Marker({
            position: this.darkstoreLocation,
            map: this.map,
            title: 'Darkstore',
            icon: {
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">
                        <circle cx="20" cy="20" r="18" fill="#FF6B6B" stroke="#fff" stroke-width="3"/>
                        <text x="20" y="25" font-family="Arial" font-size="18" fill="white" text-anchor="middle">🏪</text>
                    </svg>
                `),
                scaledSize: new google.maps.Size(40, 40),
                anchor: new google.maps.Point(20, 20)
            }
        });

        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div class="info-window">
                    <h6>🏪 Darkstore</h6>
                    <p>Main Distribution Center</p>
                    <small>Lat: ${this.darkstoreLocation.lat}, Lng: ${this.darkstoreLocation.lng}</small>
                </div>
            `
        });

        darkstoreMarker.addListener('click', () => {
            this.closeAllInfoWindows();
            infoWindow.open(this.map, darkstoreMarker);
        });

        this.markers['darkstore'] = darkstoreMarker;
        this.infoWindows['darkstore'] = infoWindow;
    }

    // Setup event listeners
    setupEventListeners() {
        // Real-time tracking toggle
        const realtimeToggle = document.getElementById('realtime-toggle-text');
        if (realtimeToggle) {
            realtimeToggle.addEventListener('click', () => {
                this.toggleRealTimeTracking();
            });
        }

        // Simulation toggle
        const simulationToggle = document.getElementById('simulation-toggle');
        if (simulationToggle) {
            simulationToggle.addEventListener('click', () => {
                this.toggleSimulation();
            });
        }

        // Generate routes and simulate button (new button needed in HTML)
        const generateAndSimulateButton = document.getElementById('generate-and-simulate-routes');
        if (generateAndSimulateButton) {
            generateAndSimulateButton.addEventListener('click', () => {
                this.generateAndSimulateRoutes();
            });
        }

        // Refresh button
        const refreshButton = document.getElementById('refresh-tracking');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.refreshTracking();
            });
        }

        // Center map button
        const centerMapButton = document.getElementById('center-map');
        if (centerMapButton) {
            centerMapButton.addEventListener('click', () => {
                this.centerMapOnAgents();
            });
        }

        // Show all deliveries button
        const showDeliveriesButton = document.getElementById('show-deliveries');
        if (showDeliveriesButton) {
            showDeliveriesButton.addEventListener('click', () => {
                this.showAllDeliveryLocations();
            });
        }

        // Generate routes button
        const generateRoutesButton = document.getElementById('generate-routes');
        if (generateRoutesButton) {
            generateRoutesButton.addEventListener('click', () => {
                this.generateAllRoutes();
            });
        }

        // Show optimized routes button
        const showOptimizedRoutesButton = document.getElementById('show-optimized-routes');
        if (showOptimizedRoutesButton) {
            showOptimizedRoutesButton.addEventListener('click', () => {
                this.showOptimizedRoutes();
            });
        }

        // Toggle route visibility
        const toggleRoutesButton = document.getElementById('toggle-routes');
        if (toggleRoutesButton) {
            toggleRoutesButton.addEventListener('click', () => {
                this.toggleRouteVisibility();
            });
        }
    }

    // NEW FUNCTION: Toggle simulation
    async toggleSimulation() {
        this.showLoadingOverlay('Toggling Simulation...');
        try {
            let endpoint = this.isSimulationActive ? API_CONFIG.ENDPOINTS.SIMULATION_STOP : API_CONFIG.ENDPOINTS.SIMULATION_START;
            let message = this.isSimulationActive ? 'Stopping simulation...' : 'Starting simulation...';

            console.log(message);
            const response = await fetch(buildApiUrl(endpoint), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (data.success) {
                this.isSimulationActive = data.simulation_active;
                this.showNotification(data.message, 'success');
                this.updateSimulationControls(); // Update UI
                
                if (this.isSimulationActive) {
                    // Start animations for all agents with routes
                    this.startAllAgentAnimations();
                    this.startRealTimeTracking(3000); // Also restart real-time tracking with a faster interval
                } else {
                    // Stop all animations
                    this.stopAllAgentAnimations();
                    this.stopRealTimeTracking(); // Stop real-time tracking if simulation is off
                }
            } else {
                this.showNotification(`Error: ${data.error || data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error toggling simulation:', error);
            this.showNotification('Error toggling simulation: ' + error.message, 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    // NEW FUNCTION: Update simulation controls UI
    updateSimulationControls() {
        const simulationToggle = document.getElementById('simulation-toggle');
        const simulationStatusElement = document.getElementById('simulation-status');

        if (this.isSimulationActive) {
            simulationToggle.textContent = 'Stop Simulation';
            simulationToggle.classList.remove('btn-outline-success');
            simulationToggle.classList.add('btn-danger');
            simulationStatusElement.textContent = 'Active';
            simulationStatusElement.className = 'badge bg-success';
        } else {
            simulationToggle.textContent = 'Start Simulation';
            simulationToggle.classList.remove('btn-danger');
            simulationToggle.classList.add('btn-outline-success');
            simulationStatusElement.textContent = 'Inactive';
            simulationStatusElement.className = 'badge bg-secondary';
        }
    }

    // NEW FUNCTION: Check simulation status on startup
    async checkSimulationStatus() {
        try {
            console.log('Checking simulation status...');
            const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.SIMULATION_STATUS));
            const data = await response.json();
            if (data.success) {
                this.isSimulationActive = data.simulation_active;
                this.updateSimulationControls();
                if (this.isSimulationActive) {
                    console.log('Simulation is active. Starting agent animations...');
                    this.startAllAgentAnimations();
                    this.startRealTimeTracking(3000); // Keep polling if simulation is active
                } else {
                    console.log('Simulation is inactive.');
                }
            }
        } catch (error) {
            console.error('Error checking simulation status:', error);
            this.showNotification('Could not retrieve simulation status.', 'error');
        }
    }

    // NEW FUNCTION: Start animations for all agents
    startAllAgentAnimations() {
        console.log('Starting animations for all agents...');
        this.agentData.forEach((agent, index) => {
            if (!agent.route_points || agent.route_points.length === 0) {
                console.log(`No route points for agent ${agent.agent_id}, skipping animation`);
                return;
            }
            
            // Handle both array format [lat, lng] and object format {lat, lng}
            const pathCoordinates = agent.route_points.map(point => {
                if (Array.isArray(point)) {
                    // Handle [lat, lng] array format from backend
                    return {
                        lat: parseFloat(point[0]),
                        lng: parseFloat(point[1])
                    };
                } else {
                    // Handle {lat, lng} object format
                    return {
                        lat: parseFloat(point.lat),
                        lng: parseFloat(point.lng)
                    };
                }
            });
            
            console.log(`Setting up animation for agent ${agent.agent_id} with ${pathCoordinates.length} points`);
            this.animateAgentPath(agent.agent_id, pathCoordinates, this.routeColors[index % this.routeColors.length]);
            this.startAgentAnimation(agent.agent_id);
        });
    }

    // NEW FUNCTION: Stop animations for all agents
    stopAllAgentAnimations() {
    console.log('Stopping all agent animations...');
    
    Object.keys(this.pathAnimations).forEach(agentId => {
        this.stopAgentAnimation(agentId);
    });
   }

    // Load initial tracking data
    async loadInitialTrackingData() {
        try {
            console.log('Loading initial tracking data...');
            this.showLoadingOverlay();
            await this.refreshTracking();
            this.hideLoadingOverlay();
        } catch (error) {
            console.error('Error loading initial tracking data:', error);
            this.showNotification('Error loading tracking data', 'error');
            this.hideLoadingOverlay();
        }
    }

    // Enhanced refresh tracking with better simulation support
    async refreshTracking() {
        try {
            console.log('Refreshing tracking data...');
            
            // Use the dashboard endpoint for comprehensive data
            const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.DASHBOARD), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received dashboard data:', data);

            if (data.success && data.dashboard) {
                this.agentData = data.dashboard.live_tracking || [];
                this.isSimulationActive = data.dashboard.simulation.active; // Update simulation status
                console.log(`Found ${this.agentData.length} active agents, Simulation Active: ${this.isSimulationActive}`);
                
                this.updateTrackingDisplay();
                this.updateStats();
                this.updateSimulationControls(); // New call to update UI based on simulation status
                
                // If simulation is active, also refresh the main dashboard
                if (this.isSimulationActive) {
                    this.refreshMainDashboard();
                }
                
                this.showNotification(`Tracking data refreshed - ${this.agentData.length} active agents`, 'success');
            } else {
                throw new Error(data.error || 'Failed to fetch dashboard data');
            }
        } catch (error) {
            console.error('Error refreshing tracking:', error);
            this.showNotification('Error refreshing tracking data: ' + error.message, 'error');
        }
    }

    // NEW FUNCTION: Refresh main dashboard to show updated order counts
    async refreshMainDashboard() {
        try {
            const response = await fetch(buildApiUrl('/api/dashboard'), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Update dashboard statistics
                    this.updateDashboardStats(data);
                    console.log('Main dashboard refreshed during simulation');
                }
            }
        } catch (error) {
            console.error('Error refreshing main dashboard:', error);
        }
    }

    // NEW FUNCTION: Update dashboard statistics
    updateDashboardStats(data) {
        const stats = data.stats || {};
        
        // Update order counts
        const totalOrdersElement = document.getElementById('total-orders');
        const unpickedElement = document.getElementById('unpicked-count');
        const pickedElement = document.getElementById('picked-count');
        const deliveredElement = document.getElementById('delivered-count');
        const delayedElement = document.getElementById('delayed-count');
        
        if (totalOrdersElement) totalOrdersElement.textContent = stats.total_orders || 0;
        if (unpickedElement) unpickedElement.textContent = stats.unpicked_orders || 0;
        if (pickedElement) pickedElement.textContent = stats.picked_orders || 0;
        if (deliveredElement) deliveredElement.textContent = stats.delivered_orders || 0;
        if (delayedElement) delayedElement.textContent = stats.delayed_orders || 0;
        
        console.log('Dashboard stats updated:', stats);
    }

    // Update tracking display
    updateTrackingDisplay() {
        console.log('Updating tracking display...');
        
        // Clear existing markers (except darkstore)
        this.clearAgentMarkers();

        // Add agent markers and routes
        this.agentData.forEach((agent, index) => {
            console.log(`Processing agent ${index + 1}:`, agent);
            
            if (agent && agent.current_location) {
                this.addAgentMarker(agent, index);
                this.addOptimizedRoute(agent, index);
                this.addDeliveryLocationMarkers(agent);
            } else {
                console.warn('Invalid agent data:', agent);
            }
        });

        // Update agent details panel
        this.updateAgentDetailsPanel();
        
        // Update route information table
        this.updateRouteInfoTable();
        
        // Update active deliveries table
        this.updateActiveDeliveriesTable();
        
        // Update stats
        this.updateStats();
        
        console.log('✅ Tracking display updated successfully');
    }

    // Add agent marker
    addAgentMarker(agent, index) {
        try {
            if (!agent.current_location || !agent.current_location.lat || !agent.current_location.lng) {
                console.warn('Invalid agent location:', agent);
                return;
            }

            const position = {
                lat: parseFloat(agent.current_location.lat),
                lng: parseFloat(agent.current_location.lng)
            };

            console.log(`Adding marker for agent ${agent.agent_id} at position:`, position);

            const marker = new google.maps.Marker({
                position: position,
                map: this.map,
                title: `${agent.agent_name} (${agent.agent_id})`,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
                            <circle cx="18" cy="18" r="16" fill="#4CAF50" stroke="#fff" stroke-width="2"/>
                            <text x="18" y="23" font-family="Arial" font-size="16" fill="white" text-anchor="middle">🚚</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(36, 36),
                    anchor: new google.maps.Point(18, 18)
                }
            });

            const infoWindow = new google.maps.InfoWindow({
                content: this.createAgentInfoWindowContent(agent)
            });

            marker.addListener('click', () => {
                this.closeAllInfoWindows();
                infoWindow.open(this.map, marker);
            });

            this.markers[agent.agent_id] = marker;
            this.infoWindows[agent.agent_id] = infoWindow;
            
            console.log(`Agent marker added successfully for ${agent.agent_id}`);
        } catch (error) {
            console.error('Error adding agent marker:', error);
        }
    }

    // Add optimized route using Directions API
    // Add optimized route using Directions API or draw a polyline
   // Fixed function for adding optimized routes with proper highlighting
addOptimizedRoute(agent, index) {
    try {
        if (!agent.route_points || agent.route_points.length === 0) {
            console.log(`No route points for agent ${agent.agent_id}`);
            return;
        }

        const routeColor = this.routeColors[index % this.routeColors.length];
        
        // Clear previous routes for this agent
        if (this.directionsRenderer[agent.agent_id]) {
            this.directionsRenderer[agent.agent_id].setMap(null);
            delete this.directionsRenderer[agent.agent_id];
        }
        
        if (this.polylines[agent.agent_id]) {
            this.polylines[agent.agent_id].setMap(null);
            delete this.polylines[agent.agent_id];
        }

        // Handle both array format [lat, lng] and object format {lat, lng}
        const pathCoordinates = agent.route_points.map(point => {
            if (Array.isArray(point)) {
                // Handle [lat, lng] array format from backend
                return {
                    lat: parseFloat(point[0]),
                    lng: parseFloat(point[1])
                };
            } else {
                // Handle {lat, lng} object format
                return {
                    lat: parseFloat(point.lat),
                    lng: parseFloat(point.lng)
                };
            }
        });

        console.log(`Processing route for agent ${agent.agent_id}:`, {
            originalPoints: agent.route_points.length,
            processedPoints: pathCoordinates.length,
            samplePoint: pathCoordinates[0]
        });

        // Create the main route polyline (visible)
        const routePolyline = new google.maps.Polyline({
            path: pathCoordinates,
            geodesic: true,
            strokeColor: routeColor,
            strokeOpacity: 0.8,
            strokeWeight: 4,
            map: this.map,
            icons: [{
                icon: {
                    path: 'M 0,-1 0,1',
                    strokeOpacity: 1,
                    scale: 3
                },
                offset: '0',
                repeat: '20px'
            }]
        });
        
        this.polylines[agent.agent_id] = routePolyline;

        // Set up animation path
        this.setupAgentAnimation(agent.agent_id, pathCoordinates, routeColor);

        console.log(`Route added for agent ${agent.agent_id} with ${pathCoordinates.length} points`);

    } catch (error) {
        console.error('Error adding optimized route:', error);
    }
}

    setupAgentAnimation(agentId, pathCoordinates, color) {
        // Clear existing animation
        if (this.animatedPaths[agentId]) {
            this.animatedPaths[agentId].setMap(null);
            delete this.animatedPaths[agentId];
        }

        // Stop any existing animation
        this.stopAgentAnimation(agentId);

        // Create animated polyline (initially empty)
        const animatedPolyline = new google.maps.Polyline({
            path: [],
            geodesic: true,
            strokeColor: color,
            strokeOpacity: 1.0,
            strokeWeight: 6,
            map: this.map,
            zIndex: 10 // Higher z-index to appear above static route
        });

        this.animatedPaths[agentId] = animatedPolyline;

        // Store animation data
        this.pathAnimations[agentId] = {
            fullPath: pathCoordinates,
            currentStep: 0,
            intervalId: null,
            isAnimating: false
        };

        console.log(`Animation setup complete for agent ${agentId} with ${pathCoordinates.length} points`);
        
        // If simulation is active, start animation immediately
        if (this.isSimulationActive) {
            this.startAgentAnimation(agentId);
        }
    }
    

    // NEW FUNCTION: Animate agent movement along the path
    animateAgentPath(agentId, path, color) {
        // Clear any existing animation for this agent
        if (this.animatedPaths[agentId]) {
            this.animatedPaths[agentId].setMap(null);
            delete this.animatedPaths[agentId];
        }

        // Create a new polyline for the animated path (initially empty)
        const animatedPolyline = new google.maps.Polyline({
            path: [],
            geodesic: true,
            strokeColor: color,
            strokeOpacity: 1.0,
            strokeWeight: 6,
            map: this.map
        });
        this.animatedPaths[agentId] = animatedPolyline;
        this.animationSteps[agentId] = 0; // Initialize step counter

        // Store the full path for animation
        this.pathAnimations[agentId] = {
            path: path,
            currentStep: 0,
            intervalId: null
        };

        // If simulation is active, start animating
        if (this.isSimulationActive) {
            this.startAgentAnimation(agentId);
        }
    }

    // NEW FUNCTION: Start animation for a single agent
    startAgentAnimation(agentId) {
        const animationData = this.pathAnimations[agentId];
        const agentMarker = this.markers[agentId];
        
        if (!animationData || !agentMarker || animationData.isAnimating) {
            console.log(`Cannot start animation for agent ${agentId}:`, {
                hasAnimationData: !!animationData,
                hasMarker: !!agentMarker,
                isAnimating: animationData?.isAnimating
            });
            return;
        }

        console.log(`Starting animation for agent ${agentId}`);
        animationData.isAnimating = true;
        animationData.currentStep = 0;

        // Reset animated path
        this.animatedPaths[agentId].setPath([]);

        animationData.intervalId = setInterval(() => {
            if (animationData.currentStep < animationData.fullPath.length) {
                const currentPosition = animationData.fullPath[animationData.currentStep];
                
                // Move marker to current position
                agentMarker.setPosition(currentPosition);
                
                // Add point to animated path
                const animatedPath = this.animatedPaths[agentId].getPath();
                animatedPath.push(new google.maps.LatLng(currentPosition.lat, currentPosition.lng));
                
                // Update agent's current location in data
                const agent = this.agentData.find(a => a.agent_id === agentId);
                if (agent) {
                    agent.current_location = currentPosition;
                    
                    // Update info window if it's open
                    if (this.infoWindows[agentId] && this.infoWindows[agentId].getMap()) {
                        this.infoWindows[agentId].setContent(this.createAgentInfoWindowContent(agent));
                    }
                }
                
                animationData.currentStep++;
                
            } else {
                // Animation complete - restart from beginning for continuous simulation
                console.log(`Agent ${agentId} completed route, restarting...`);
                animationData.currentStep = 0;
                this.animatedPaths[agentId].setPath([]);
            }
        }, 1000); // Animation speed: 1000ms per step for better visibility

        console.log(`Animation started for agent ${agentId}`);
    }

    // NEW FUNCTION: Stop animation for a single agent
    stopAgentAnimation(agentId) {
        if (this.pathAnimations[agentId] && this.pathAnimations[agentId].intervalId) {
            clearInterval(this.pathAnimations[agentId].intervalId);
            this.pathAnimations[agentId].intervalId = null;
            console.log(`Stopped animation for agent ${agentId}`);
        }
    }

    // Fallback: Add simple polyline route
    addSimpleRoute(agent, color) {
        try {
            if (!agent.route_points || agent.route_points.length === 0) {
                return;
            }

            const routeCoordinates = agent.route_points.map(point => ({
                lat: parseFloat(point.lat),
                lng: parseFloat(point.lng)
            }));

            const routePath = new google.maps.Polyline({
                path: routeCoordinates,
                geodesic: true,
                strokeColor: color,
                strokeOpacity: 0.8,
                strokeWeight: 3
            });

            routePath.setMap(this.map);
            this.polylines[agent.agent_id] = routePath;
            
            console.log(`Simple route added for agent ${agent.agent_id}`);
        } catch (error) {
            console.error('Error adding simple route:', error);
        }
    }

    // Add delivery location markers with enhanced styling
    addDeliveryLocationMarkers(agent) {
        try {
            if (!agent.delivery_locations || agent.delivery_locations.length === 0) {
                console.log(`No delivery locations for agent ${agent.agent_id}`);
                return;
            }

            agent.delivery_locations.forEach((delivery, index) => {
                if (!delivery.location || !delivery.location.lat || !delivery.location.lng) {
                    console.warn('Invalid delivery location:', delivery);
                    return;
                }

                const position = {
                    lat: parseFloat(delivery.location.lat),
                    lng: parseFloat(delivery.location.lng)
                };

                const statusColor = this.getDeliveryStatusColor(delivery.status);
                
                const marker = new google.maps.Marker({
                    position: position,
                    map: this.map,
                    title: `Delivery ${index + 1} - Order ${delivery.order_id}`,
                    icon: {
                        url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30" width="30" height="30">
                                <circle cx="15" cy="15" r="13" fill="${statusColor}" stroke="#fff" stroke-width="2"/>
                                <text x="15" y="19" font-family="Arial" font-size="12" fill="white" text-anchor="middle" font-weight="bold">${index + 1}</text>
                            </svg>
                        `),
                        scaledSize: new google.maps.Size(30, 30),
                        anchor: new google.maps.Point(15, 15)
                    }
                });

                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div class="info-window">
                            <h6>📦 Delivery Stop ${index + 1}</h6>
                            <p><strong>Order ID:</strong> ${delivery.order_id}</p>
                            <p><strong>Status:</strong> <span class="badge bg-${this.getStatusColor(delivery.status)}">${delivery.status}</span></p>
                            <p><strong>Agent:</strong> ${agent.agent_name}</p>
                            <p><strong>Sequence:</strong> ${index + 1} of ${agent.delivery_locations.length}</p>
                            <small>Lat: ${delivery.location.lat}, Lng: ${delivery.location.lng}</small>
                        </div>
                    `
                });

                marker.addListener('click', () => {
                    this.closeAllInfoWindows();
                    infoWindow.open(this.map, marker);
                });

                const markerId = `delivery_${agent.agent_id}_${index}`;
                this.markers[markerId] = marker;
                this.infoWindows[markerId] = infoWindow;
            });
            
            console.log(`Added ${agent.delivery_locations.length} delivery markers for agent ${agent.agent_id}`);
        } catch (error) {
            console.error('Error adding delivery location markers:', error);
        }
    }

    // Get delivery status color
    getDeliveryStatusColor(status) {
        switch (status.toLowerCase()) {
            case 'delivered': return '#4CAF50';
            case 'in_transit': return '#FF9800';
            case 'assigned': return '#2196F3';
            case 'delayed': return '#F44336';
            default: return '#757575';
        }
    }

    // Create enhanced agent info window content
    createAgentInfoWindowContent(agent, routeInfo = null) {
        const routeDetails = routeInfo ? `
            <div class="route-details">
                <p><strong>🛣️ Route:</strong> ${routeInfo.distance} (${routeInfo.duration})</p>
                <p><strong>Optimized:</strong> ${routeInfo.optimized ? '✅ Yes' : '❌ No'}</p>
            </div>
        ` : '';

        return `
            <div class="info-window">
                <h6>🚚 ${agent.agent_name}</h6>
                <p><strong>ID:</strong> ${agent.agent_id}</p>
                <p><strong>Status:</strong> <span class="badge bg-success">${agent.status}</span></p>
                <p><strong>Deliveries:</strong> ${agent.total_deliveries}</p>
                <p><strong>Assigned Orders:</strong> ${agent.assigned_orders ? agent.assigned_orders.join(', ') : 'None'}</p>
                ${routeDetails}
                <div class="agent-actions">
                    <button class="btn btn-sm btn-primary" onclick="trackingDashboard.centerOnAgent('${agent.agent_id}')">
                        🎯 Center
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="trackingDashboard.rerouteAgent('${agent.agent_id}')">
                        🔄 Reroute
                    </button>
                    <button class="btn btn-sm btn-info" onclick="trackingDashboard.showAgentRoute('${agent.agent_id}')">
                        🛣️ Route
                    </button>
                </div>
            </div>
        `;
    }

    // Show optimized routes for all agents
    showOptimizedRoutes() {
        console.log('Showing optimized routes for all agents...');
        
        this.agentData.forEach((agent, index) => {
            if (agent && agent.route_points && agent.route_points.length > 0) {
                // Hide existing simple routes
                if (this.polylines[agent.agent_id]) {
                    this.polylines[agent.agent_id].setMap(null);
                }
                
                // Show optimized route
                this.addOptimizedRoute(agent, index);
            }
        });
        
        this.showNotification('Optimized routes displayed for all agents', 'success');
    }

    // Toggle route visibility
    toggleRouteVisibility() {
    const button = document.getElementById('toggle-routes');
    const isVisible = button.textContent.includes('Hide');
    
    // Toggle main route polylines
    Object.values(this.polylines).forEach(polyline => {
        polyline.setMap(isVisible ? null : this.map);
    });
    
    // Toggle animated paths
    Object.values(this.animatedPaths).forEach(polyline => {
        polyline.setMap(isVisible ? null : this.map);
    });
    
    // Toggle DirectionsRenderer (if any)
    Object.values(this.directionsRenderer).forEach(renderer => {
        renderer.setMap(isVisible ? null : this.map);
    });
    
    button.textContent = isVisible ? '👁️ Show Routes' : '🙈 Hide Routes';
    this.showNotification(`Routes ${isVisible ? 'hidden' : 'shown'}`, 'info');
}

    // Show specific agent route
    showAgentRoute(agentId) {
    const agent = this.agentData.find(a => a.agent_id === agentId);
    if (!agent) {
        this.showNotification('Agent not found', 'error');
        return;
    }

    // Center on agent
    this.centerOnAgent(agentId);
    
    // Highlight the route
    if (this.polylines[agentId]) {
        const originalPolyline = this.polylines[agentId];
        
        // Store original options
        const originalOptions = {
            strokeColor: originalPolyline.get('strokeColor'),
            strokeWeight: originalPolyline.get('strokeWeight'),
            strokeOpacity: originalPolyline.get('strokeOpacity')
        };
        
        // Apply highlight
        originalPolyline.setOptions({
            strokeColor: '#FFD700',
            strokeWeight: 8,
            strokeOpacity: 1.0,
            zIndex: 100
        });
        
        // Reset after 3 seconds
        setTimeout(() => {
            originalPolyline.setOptions(originalOptions);
        }, 3000);
    }
    
    // Also highlight animated path if it exists
    if (this.animatedPaths[agentId]) {
        const animatedPolyline = this.animatedPaths[agentId];
        const originalColor = animatedPolyline.get('strokeColor');
        
        animatedPolyline.setOptions({
            strokeColor: '#FFD700',
            strokeWeight: 8,
            zIndex: 101
        });
        
        // Reset after 3 seconds
        setTimeout(() => {
            animatedPolyline.setOptions({
                strokeColor: originalColor,
                strokeWeight: 6
            });
        }, 3000);
    }
    
    this.showNotification(`Highlighting route for ${agent.agent_name}`, 'info');
}

    // Update agent details panel
    // Update agent details panel
    updateAgentDetailsPanel() {
        const agentsGrid = document.getElementById('agent-details-grid');
        if (!agentsGrid) {
            console.warn('Agent details grid not found');
            return;
        }
        
        agentsGrid.innerHTML = ''; // Clear previous entries

        if (this.agentData.length === 0) {
            agentsGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle me-2"></i>
                        No active delivery agents found.
                    </div>
                </div>
            `;
            return;
        }

        this.agentData.forEach((agent, index) => {
            const totalOrders = agent.assigned_orders ? agent.assigned_orders.length : 0;
            const routeStatus = agent.route_points && agent.route_points.length > 0 ? 'Optimized Route Available' : 'No Route';
            const routeDistance = agent.route_details ? agent.route_details.distance : 'N/A';
            const routeDuration = agent.route_details ? agent.route_details.duration : 'N/A';
            const statusColor = agent.status === 'available' ? 'success' : 'warning';

            const agentCard = document.createElement('div');
            agentCard.className = 'col-md-6 col-lg-4 mb-3';
            agentCard.innerHTML = `
                <div class="card bg-dark text-white border-primary">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">🚚 ${agent.agent_name || agent.name || 'Unknown Agent'}</h6>
                        <span class="badge bg-${statusColor}">${agent.status || 'Unknown'}</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Agent ID:</small><br>
                                <strong>${agent.agent_id || agent.id || 'N/A'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Orders:</small><br>
                                <strong>${totalOrders}</strong>
                            </div>
                        </div>
                        <hr class="my-2">
                        <div class="row">
                            <div class="col-12">
                                <small class="text-muted">Route Status:</small><br>
                                <span class="badge bg-info">${routeStatus}</span>
                            </div>
                        </div>
                        ${routeDistance !== 'N/A' ? `
                        <div class="row mt-2">
                            <div class="col-6">
                                <small class="text-muted">Distance:</small><br>
                                <strong>${routeDistance}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Duration:</small><br>
                                <strong>${routeDuration}</strong>
                            </div>
                        </div>
                        ` : ''}
                        <div class="mt-3">
                            <button class="btn btn-sm btn-outline-primary w-100 view-agent-btn" data-agent-id="${agent.agent_id || agent.id}">
                                <i class="fas fa-map-marker-alt me-1"></i>View on Map
                            </button>
                        </div>
                    </div>
                </div>
            `;
            agentsGrid.appendChild(agentCard);

            // Add event listener for view button
            agentCard.querySelector('.view-agent-btn').addEventListener('click', (event) => {
                const agentId = event.target.dataset.agentId;
                const selectedAgent = this.agentData.find(a => (a.agent_id || a.id) === agentId);
                if (selectedAgent && this.markers[agentId]) {
                    this.map.panTo(this.markers[agentId].getPosition());
                    this.map.setZoom(15);
                    this.closeAllInfoWindows();
                    if (this.infoWindows[agentId]) {
                        this.infoWindows[agentId].open(this.map, this.markers[agentId]);
                    }
                }
            });
        });
    }

    // Update route information table
    updateRouteInfoTable() {
        const tbody = document.getElementById('route-info-table');
        if (!tbody) {
            console.warn('Route info table not found');
            return;
        }

        tbody.innerHTML = '';

        this.agentData.forEach(agent => {
            const agentName = agent.agent_name || agent.name || 'Unknown Agent';
            const agentId = agent.agent_id || agent.id || 'N/A';
            const status = agent.status || 'Unknown';
            const currentLocation = agent.current_location ? 
                `${agent.current_location.lat?.toFixed(4) || 'N/A'}, ${agent.current_location.lng?.toFixed(4) || 'N/A'}` : 
                'Dark Store';
            
            const nextDelivery = agent.delivery_locations && agent.delivery_locations.length > 0 ? 
                agent.delivery_locations[0].order_id : 'None';
            
            const routeDistance = agent.route_details ? agent.route_details.distance : 'N/A';
            const routeDuration = agent.route_details ? agent.route_details.duration : 'N/A';
            const deliveriesRemaining = agent.delivery_locations ? agent.delivery_locations.length : 0;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <strong>${agentName}</strong><br>
                    <small class="text-muted">${agentId}</small>
                </td>
                <td>
                    <span class="badge bg-${status === 'available' ? 'success' : 'warning'}">${status}</span>
                </td>
                <td>${currentLocation}</td>
                <td>${nextDelivery}</td>
                <td>${routeDistance}</td>
                <td>${routeDuration}</td>
                <td>
                    <span class="badge bg-info">${deliveriesRemaining}</span>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // Update active deliveries table
    updateActiveDeliveriesTable() {
        const tbody = document.getElementById('active-deliveries-table');
        if (!tbody) {
            console.warn('Active deliveries table not found');
            return;
        }

        tbody.innerHTML = '';

        this.agentData.forEach(agent => {
            if (agent.delivery_locations && agent.delivery_locations.length > 0) {
                agent.delivery_locations.forEach((delivery, index) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${delivery.order_id}</td>
                        <td>${agent.agent_name || agent.name || 'Unknown Agent'}</td>
                        <td>Customer ${index + 1}</td>
                        <td>${delivery.location.lat.toFixed(4)}, ${delivery.location.lng.toFixed(4)}</td>
                        <td>
                            <span class="badge bg-info">Optimized Route</span>
                        </td>
                        <td>
                            <span class="badge bg-${this.getStatusColor(delivery.status)}">${delivery.status}</span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="trackingDashboard.trackOrder('${delivery.order_id}')">
                                📍 Track
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        });
    }

    // Get status color for badge
    getStatusColor(status) {
        switch (status.toLowerCase()) {
            case 'delivered': return 'success';
            case 'in_transit': return 'warning';
            case 'assigned': return 'info';
            case 'delayed': return 'danger';
            default: return 'secondary';
        }
    }

    // Update stats
    updateStats() {
        const activeAgentsCount = this.agentData.length;
        const totalDeliveries = this.agentData.reduce((sum, agent) => sum + agent.total_deliveries, 0);

        const activeAgentsElement = document.getElementById('active-agents-count');
        const activeDeliveriesElement = document.getElementById('active-deliveries-count');
        const simulationStatusElement = document.getElementById('simulation-status');

        if (activeAgentsElement) {
            activeAgentsElement.textContent = activeAgentsCount;
        }

        if (activeDeliveriesElement) {
            activeDeliveriesElement.textContent = totalDeliveries;
        }

        if (simulationStatusElement) {
            simulationStatusElement.textContent = this.isSimulationActive ? 'Running' : 'Stopped';
            simulationStatusElement.className = `badge bg-${this.isSimulationActive ? 'success' : 'secondary'}`;
        }
    }

    // Clear agent markers (except darkstore)
    // Clear existing agent markers and routes (except darkstore)
    clearAgentMarkers() {
        console.log('Clearing existing agent markers and routes...');
        // Clear DirectionsRenderers
        for (const agentId in this.directionsRenderer) {
            if (this.directionsRenderer.hasOwnProperty(agentId)) {
                this.directionsRenderer[agentId].setMap(null);
                delete this.directionsRenderer[agentId];
            }
        }
        // Clear simple polylines (if any were drawn as fallback)
        for (const agentId in this.polylines) {
            if (this.polylines.hasOwnProperty(agentId)) {
                this.polylines[agentId].setMap(null);
                delete this.polylines[agentId];
            }
        }
        // Clear animated paths
        for (const agentId in this.animatedPaths) {
            if (this.animatedPaths.hasOwnProperty(agentId)) {
                this.animatedPaths[agentId].setMap(null);
                delete this.animatedPaths[agentId];
            }
        }

        // Clear markers (excluding darkstore)
        for (const agentId in this.markers) {
            if (this.markers.hasOwnProperty(agentId) && agentId !== 'darkstore') {
                this.markers[agentId].setMap(null);
                delete this.markers[agentId];
                if (this.infoWindows[agentId]) {
                    this.infoWindows[agentId].close();
                    delete this.infoWindows[agentId];
                }
            }
        }
        // Clear delivery location markers as they are recreated per agent
        // A more robust solution might involve a separate collection for them if they are truly global
        this.deliveryLocations.forEach(marker => marker.setMap(null));
        this.deliveryLocations = [];
        console.log('Cleared all dynamic markers and routes.');
    }



    // Close all info windows
    closeAllInfoWindows() {
        Object.values(this.infoWindows).forEach(infoWindow => {
            infoWindow.close();
        });
    }

    // Toggle real-time tracking
    toggleRealTimeTracking() {
        const realtimeToggleSwitch = document.getElementById('realtime-toggle-switch');
        const realtimeToggleText = document.getElementById('realtime-toggle-text');

        this.isRealTimeActive = !this.isRealTimeActive; // Toggle the state

        if (this.isRealTimeActive) {
            realtimeToggleText.textContent = 'ON';
            realtimeToggleSwitch.checked = true;
            this.startRealTimeTracking();
            this.showNotification('Real-time tracking started.', 'info');
        } else {
            realtimeToggleText.textContent = 'OFF';
            realtimeToggleSwitch.checked = false;
            this.stopRealTimeTracking();
            this.showNotification('Real-time tracking stopped.', 'info');
        }
    }

    startRealTimeTracking(interval = 5000) { // Default 5 seconds, can be faster for simulation
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
        }
        
        this.isRealTimeActive = true;
        this.realTimeInterval = setInterval(async () => {
            try {
                await this.refreshTracking();
                
                // If simulation is active, update agent positions more frequently
                if (this.isSimulationActive) {
                    this.updateAgentPositions();
                }
            } catch (error) {
                console.error('Error in real-time tracking:', error);
            }
        }, interval);
        
        console.log(`Real-time tracking started with ${interval}ms interval`);
        this.updateRealTimeStatus();
    }

    stopRealTimeTracking() {
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
            this.realTimeInterval = null;
            console.log('Real-time tracking stopped.');
        }
    }

    // Enhanced updateAgentPositions with better logging
    updateAgentPositions() {
        let updatedCount = 0;
        
        this.agentData.forEach(agent => {
            if (agent.current_location && this.markers[agent.agent_id]) {
                const newPosition = {
                    lat: parseFloat(agent.current_location.lat),
                    lng: parseFloat(agent.current_location.lng)
                };
                
                // Get current marker position
                const currentPosition = this.markers[agent.agent_id].getPosition();
                const currentLat = currentPosition.lat();
                const currentLng = currentPosition.lng();
                
                // Only update if position actually changed
                if (Math.abs(currentLat - newPosition.lat) > 0.0001 || 
                    Math.abs(currentLng - newPosition.lng) > 0.0001) {
                    
                    // Update marker position
                    this.markers[agent.agent_id].setPosition(newPosition);
                    
                    // Update info window content if open
                    if (this.infoWindows[agent.agent_id] && this.infoWindows[agent.agent_id].getMap()) {
                        this.infoWindows[agent.agent_id].setContent(this.createAgentInfoWindowContent(agent));
                    }
                    
                    updatedCount++;
                    console.log(`Updated position for agent ${agent.agent_id}:`, newPosition);
                }
            }
        });
        
        if (updatedCount > 0) {
            console.log(`Updated positions for ${updatedCount} agents during simulation`);
        }
    }

    // Enhanced toggle simulation with proper animation handling
    async toggleSimulation() {
        this.showLoadingOverlay('Toggling Simulation...');
        
        try {
            const endpoint = this.isSimulationActive ? 
                API_CONFIG.ENDPOINTS.SIMULATION_STOP : 
                API_CONFIG.ENDPOINTS.SIMULATION_START;
                
            const response = await fetch(buildApiUrl(endpoint), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();

            if (data.success) {
                this.isSimulationActive = data.simulation_active;
                this.updateSimulationControls();
                
                if (this.isSimulationActive) {
                    // Start simulation with faster real-time updates
                    this.startRealTimeTracking(2000); // 2-second updates during simulation
                    this.showNotification('Simulation started - agents are now moving!', 'success');
                    
                    // Generate routes if not already present
                    if (this.agentData.length > 0 && !this.agentData.some(agent => agent.route_points)) {
                        await this.generateAllRoutes();
                    }
                } else {
                    // Stop simulation
                    this.stopRealTimeTracking();
                    this.showNotification('Simulation stopped', 'success');
                }
            } else {
                this.showNotification(`Error: ${data.error || data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error toggling simulation:', error);
            this.showNotification('Error toggling simulation: ' + error.message, 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    // Enhanced startAllAgentAnimations for better simulation support
    startAllAgentAnimations() {
        console.log('Starting animations for all agents...');
        this.agentData.forEach((agent, index) => {
            if (!agent.route_points || agent.route_points.length === 0) {
                console.log(`No route points for agent ${agent.agent_id}, skipping animation`);
                return;
            }
            
            // Handle both array format [lat, lng] and object format {lat, lng}
            const pathCoordinates = agent.route_points.map(point => {
                if (Array.isArray(point)) {
                    // Handle [lat, lng] array format from backend
                    return {
                        lat: parseFloat(point[0]),
                        lng: parseFloat(point[1])
                    };
                } else {
                    // Handle {lat, lng} object format
                    return {
                        lat: parseFloat(point.lat),
                        lng: parseFloat(point.lng)
                    };
                }
            });
            
            console.log(`Setting up animation for agent ${agent.agent_id} with ${pathCoordinates.length} points`);
            this.setupAgentAnimation(agent.agent_id, pathCoordinates, this.routeColors[index % this.routeColors.length]);
        });
    }

    // Enhanced setupAgentAnimation for simulation
    setupAgentAnimation(agentId, pathCoordinates, color) {
        // Clear existing animation
        if (this.animatedPaths[agentId]) {
            this.animatedPaths[agentId].setMap(null);
            delete this.animatedPaths[agentId];
        }

        // Stop any existing animation
        this.stopAgentAnimation(agentId);

        // Create animated polyline (initially empty)
        const animatedPolyline = new google.maps.Polyline({
            path: [],
            geodesic: true,
            strokeColor: color,
            strokeOpacity: 1.0,
            strokeWeight: 6,
            map: this.map,
            zIndex: 10 // Higher z-index to appear above static route
        });

        this.animatedPaths[agentId] = animatedPolyline;

        // Store animation data
        this.pathAnimations[agentId] = {
            fullPath: pathCoordinates,
            currentStep: 0,
            intervalId: null,
            isAnimating: false
        };

        console.log(`Animation setup complete for agent ${agentId} with ${pathCoordinates.length} points`);
        
        // For simulation, we don't start the interval-based animation
        // Instead, we rely on real-time position updates from the backend
        if (this.isSimulationActive) {
            console.log(`Simulation active - agent ${agentId} will follow real-time updates`);
        }
    }

    // Enhanced updateSimulationControls
    updateSimulationControls() {
        const button = document.getElementById('simulation-toggle');
        const statusElement = document.getElementById('simulation-status');
        const indicator = document.getElementById('simulation-indicator');
        
        if (button) {
            if (this.isSimulationActive) {
                button.innerHTML = '<i class="fas fa-stop"></i> Stop Simulation';
                button.className = 'btn btn-outline-danger';
            } else {
                button.innerHTML = '<i class="fas fa-play"></i> Start Simulation';
                button.className = 'btn btn-outline-success';
            }
        }
        
        if (statusElement) {
            statusElement.textContent = this.isSimulationActive ? 'Active' : 'Inactive';
            statusElement.className = this.isSimulationActive ? 'badge bg-success' : 'badge bg-secondary';
        }
        
        if (indicator) {
            indicator.className = this.isSimulationActive ? 'fas fa-circle text-success' : 'fas fa-circle text-secondary';
        }
        
        console.log(`Simulation controls updated - Active: ${this.isSimulationActive}`);
    }

    // Check simulation status
    async checkSimulationStatus() {
        try {
            const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.SIMULATION_STATUS), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.isSimulationActive = data.simulation_active || false;
                
                const button = document.getElementById('simulation-toggle');
                if (button) {
                    button.textContent = this.isSimulationActive ? '⏹️ Stop Simulation' : '▶️ Start Simulation';
                }
                
                this.updateStats();
            }
        } catch (error) {
            console.error('Error checking simulation status:', error);
        }
    }

    // Center map on all agents
    centerMapOnAgents() {
        if (this.agentData.length === 0) {
            this.showNotification('No agents to center on', 'warning');
            return;
        }

        const bounds = new google.maps.LatLngBounds();
        
        // Include darkstore
        bounds.extend(new google.maps.LatLng(this.darkstoreLocation.lat, this.darkstoreLocation.lng));
        
        // Include all agents
        this.agentData.forEach(agent => {
            if (agent.current_location) {
                bounds.extend(new google.maps.LatLng(
                    parseFloat(agent.current_location.lat),
                    parseFloat(agent.current_location.lng)
                ));
            }
        });

        this.map.fitBounds(bounds);
        this.showNotification('Map centered on all agents', 'info');
    }

    // Center on specific agent
    centerOnAgent(agentId) {
        const agent = this.agentData.find(a => a.agent_id === agentId);
        if (!agent || !agent.current_location) {
            this.showNotification('Agent not found or no location data', 'error');
            return;
        }

        const position = new google.maps.LatLng(
            parseFloat(agent.current_location.lat),
            parseFloat(agent.current_location.lng)
        );

        this.map.setCenter(position);
        this.map.setZoom(15);
        
        // Open info window
        if (this.infoWindows[agentId]) {
            this.closeAllInfoWindows();
            this.infoWindows[agentId].open(this.map, this.markers[agentId]);
        }
        
        this.showNotification(`Centered on ${agent.agent_name}`, 'info');
    }

    // Show all delivery locations
    showAllDeliveryLocations() {
        if (this.agentData.length === 0) {
            this.showNotification('No delivery locations to display', 'warning');
            return;
        }

        const bounds = new google.maps.LatLngBounds();
        let totalDeliveries = 0;

        this.agentData.forEach(agent => {
            if (agent.delivery_locations && agent.delivery_locations.length > 0) {
                agent.delivery_locations.forEach(delivery => {
                    if (delivery.location) {
                        bounds.extend(new google.maps.LatLng(
                            parseFloat(delivery.location.lat),
                            parseFloat(delivery.location.lng)
                        ));
                        totalDeliveries++;
                    }
                });
            }
        });

        if (totalDeliveries > 0) {
            this.map.fitBounds(bounds);
            this.showNotification(`Showing ${totalDeliveries} delivery locations`, 'success');
        } else {
            this.showNotification('No delivery locations found', 'warning');
        }
    }

    // Generate all routes
    async generateAllRoutes() {
        try {
            console.log('Generating all routes...');
            this.showLoadingOverlay();
            
            const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.GENERATE_ALL), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('All routes generated successfully', 'success');
                // Refresh tracking to show new routes
                await this.refreshTracking();
            } else {
                throw new Error(data.error || 'Failed to generate routes');
            }
        } catch (error) {
            console.error('Error generating routes:', error);
            this.showNotification('Error generating routes: ' + error.message, 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    // Update real-time status
    updateRealTimeStatus() {
        const statusElement = document.getElementById('realtime-status');
        const toggleButton = document.getElementById('realtime-toggle-text');
        
        if (statusElement) {
            statusElement.textContent = this.isRealTimeActive ? 'Active' : 'Stopped';
            statusElement.className = this.isRealTimeActive ? 'badge bg-success' : 'badge bg-danger';
        }
        
        if (toggleButton) {
            toggleButton.textContent = this.isRealTimeActive ? '⏹️ Stop Real-time' : '▶️ Start Real-time';
        }
    }

    // NEW FUNCTION: Generate optimized routes and start simulation
    async generateAndSimulateRoutes() {
        this.showLoadingOverlay('Generating and Simulating Routes...');
        try {
            console.log('Calling generate and simulate routes API...');
            const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.GENERATE_AND_SIMULATE), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            console.log('Generate and simulate response:', data);

            if (data.success) {
                this.showNotification(data.message, 'success');
                this.isSimulationActive = true;
                this.updateSimulationControls();
                
                // Refresh tracking data to get the new routes
                await this.refreshTracking();
                
                // If routes were returned, update agent data
                if (data.routes) {
                    console.log('Routes received:', data.routes);
                    this.agentData.forEach(agent => {
                        if (data.routes[agent.agent_id]) {
                            agent.route_points = data.routes[agent.agent_id];
                            console.log(`Updated agent ${agent.agent_id} with route:`, agent.route_points);
                        }
                    });
                }
                
                // Start animations for all agents
                this.startAllAgentAnimations();
                this.startRealTimeTracking(3000);
            } else {
                this.showNotification(`Error generating and simulating routes: ${data.error || data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error generating and simulating routes:', error);
            this.showNotification('Error generating and simulating routes: ' + error.message, 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    // Reroute specific agent
    async rerouteAgent(agentId) {
        try {
            console.log(`Rerouting agent ${agentId}...`);
            this.showLoadingOverlay();
            
            const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.REROUTE), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors',
                body: JSON.stringify({
                    agent_id: agentId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Agent ${agentId} rerouted successfully`, 'success');
                // Refresh tracking to show new route
                await this.refreshTracking();
            } else {
                throw new Error(data.error || 'Failed to reroute agent');
            }
        } catch (error) {
            console.error('Error rerouting agent:', error);
            this.showNotification('Error rerouting agent: ' + error.message, 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    // Track specific order
    trackOrder(orderId) {
        console.log(`Tracking order ${orderId}...`);
        
        // Find the agent and delivery for this order
        let targetAgent = null;
        let targetDelivery = null;
        
        this.agentData.forEach(agent => {
            if (agent.delivery_locations) {
                const delivery = agent.delivery_locations.find(d => d.order_id === orderId);
                if (delivery) {
                    targetAgent = agent;
                    targetDelivery = delivery;
                }
            }
        });
        
        if (targetAgent && targetDelivery) {
            // Center on delivery location
            const position = new google.maps.LatLng(
                parseFloat(targetDelivery.location.lat),
                parseFloat(targetDelivery.location.lng)
            );
            
            this.map.setCenter(position);
            this.map.setZoom(16);
            
            // Find and open the delivery marker info window
            const deliveryIndex = targetAgent.delivery_locations.indexOf(targetDelivery);
            const markerId = `delivery_${targetAgent.agent_id}_${deliveryIndex}`;
            
            if (this.infoWindows[markerId]) {
                this.closeAllInfoWindows();
                this.infoWindows[markerId].open(this.map, this.markers[markerId]);
            }
            
            this.showNotification(`Tracking order ${orderId} - Assigned to ${targetAgent.agent_name}`, 'info');
        } else {
            this.showNotification(`Order ${orderId} not found`, 'error');
        }
    }

    // Show loading overlay
    showLoadingOverlay() {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading...</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }

    // Hide loading overlay
    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // Show notification
    showNotification(message, type = 'info') {
        console.log(`Notification [${type}]: ${message}`);
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show notification`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Cleanup method
    cleanup() {
        // Stop real-time tracking
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
            this.realTimeInterval = null;
        }
        
        // Stop simulation interval
        if (this.simulationInterval) {
            clearInterval(this.simulationInterval);
            this.simulationInterval = null;
        }
        
        // Clear all markers and info windows
        Object.values(this.markers).forEach(marker => {
            marker.setMap(null);
        });
        
        Object.values(this.infoWindows).forEach(infoWindow => {
            infoWindow.close();
        });
        
        // Clear directions renderers
        Object.values(this.directionsRenderer).forEach(renderer => {
            renderer.setMap(null);
        });
        
        // Clear polylines
        Object.values(this.polylines).forEach(polyline => {
            polyline.setMap(null);
        });
        
        console.log('Tracking dashboard cleaned up');
    }
}

// Initialize tracking dashboard when DOM is ready
let trackingDashboard = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing tracking dashboard...');
    trackingDashboard = new TrackingDashboard();
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (trackingDashboard) {
        trackingDashboard.cleanup();
    }
});

// CSS for loading overlay and notifications (add to your CSS file)
const additionalCSS = `
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9998;
}

.loading-spinner {
    text-align: center;
    color: white;
}

.notification {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
}

.info-window {
    padding: 10px;
    font-family: Arial, sans-serif;
}

.info-window h6 {
    margin: 0 0 10px 0;
    color: #333;
}

.info-window p {
    margin: 5px 0;
    font-size: 14px;
}

.agent-actions {
    margin-top: 10px;
}

.agent-actions .btn {
    margin: 2px;
    font-size: 12px;
}

.route-details {
    background-color: #f8f9fa;
    padding: 8px;
    border-radius: 4px;
    margin: 8px 0;
}

.agent-stats {
    display: flex;
    justify-content: space-between;
    margin: 10px 0;
}

.stat-item {
    text-align: center;
}

.stat-label {
    display: block;
    font-size: 12px;
    color: #ccc;
}

.stat-value {
    display: block;
    font-size: 16px;
    font-weight: bold;
    color: #fff;
}
`;

// Add CSS to document
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalCSS;
document.head.appendChild(styleSheet);