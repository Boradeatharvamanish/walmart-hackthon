// Enhanced Dashboard JavaScript with Interactive Features

// Global variables
let currentTab = 'dashboard';
let refreshInterval = null;
let isFullscreen = false;

// Enhanced tab switching with animations
function switchTab(tabName) {
    // Hide all tabs with fade out animation
    const allTabs = document.querySelectorAll('[id$="-tab"]');
    allTabs.forEach(tab => {
        tab.style.display = 'none';
        tab.classList.remove('fade-in');
    });

    // Remove active class from all nav links
    const allNavLinks = document.querySelectorAll('.nav-link');
    allNavLinks.forEach(link => link.classList.remove('active'));

    // Show selected tab with fade in animation
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.style.display = 'block';
        setTimeout(() => {
            selectedTab.classList.add('fade-in');
        }, 10);
    }

    // Add active class to clicked nav link
    const activeLink = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    currentTab = tabName;

    // Initialize specific tab functionality
    initializeTab(tabName);
}

// Initialize tab-specific functionality
function initializeTab(tabName) {
    switch(tabName) {
        case 'dashboard':
            loadDashboardData();
            startAutoRefresh();
            break;
        case 'orders':
            loadOrdersData();
            break;
        case 'picking':
            initializePickingDashboard();
            loadPickingData();
            break;
        case 'delivery':
            initializeDeliveryDashboard();
            loadDeliveryData();
            break;
        case 'tracking':
            if (typeof trackingDashboard !== 'undefined') {
                trackingDashboard.refreshTracking();
            }
            break;
    }
}

// Enhanced dashboard data loading
async function loadDashboardData() {
    try {
        showLoading('Loading dashboard data...');
        
        const response = await fetch('http://127.0.0.1:5000/api/dashboard');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        if (data.success) {
            updateDashboardStats(data);
            showNotification('Dashboard data loaded successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to load dashboard data');
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Error loading dashboard data: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Load picking data
async function loadPickingData() {
    try {
        console.log('Loading picking data...');
        
        const response = await fetch('http://127.0.0.1:5000/api/picking/status');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        if (data.success) {
            // Update picking dashboard with real data
            if (typeof window.pickingManager !== 'undefined') {
                window.pickingManager.updateOrders(data.orders || {});
            }
            showNotification('Picking data loaded successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to load picking data');
        }
    } catch (error) {
        console.error('Error loading picking data:', error);
        showNotification('Error loading picking data: ' + error.message, 'error');
    }
}

// Load delivery data
async function loadDeliveryData() {
    try {
        console.log('Loading delivery data...');
        
        if (typeof window.deliveryDashboard !== 'undefined') {
            await window.deliveryDashboard.refreshDeliveryData();
            showNotification('Delivery data loaded successfully', 'success');
        } else {
            console.warn('Delivery dashboard not initialized');
        }
    } catch (error) {
        console.error('Error loading delivery data:', error);
        showNotification('Error loading delivery data: ' + error.message, 'error');
    }
}

// Update dashboard statistics with animations
function updateDashboardStats(data) {
    console.log('📊 Updating dashboard stats with data:', data);
    
    // Extract order statistics from the API response
    const orders = data.orders || {};
    const ordersByStatus = orders.orders_by_status || {};
    
    console.log('📋 Orders data:', orders);
    console.log('📋 Orders by status:', ordersByStatus);
    
    // Helper function to get count by status (case-insensitive)
    const getStatusCount = (statusKey) => {
        const statusVariations = [
            statusKey.toLowerCase(),
            statusKey.charAt(0).toUpperCase() + statusKey.slice(1).toLowerCase(),
            statusKey.toUpperCase()
        ];
        
        for (const variation of statusVariations) {
            if (ordersByStatus[variation] !== undefined) {
                console.log(`✅ Found ${statusKey} count: ${ordersByStatus[variation]} (using variation: ${variation})`);
                return ordersByStatus[variation];
            }
        }
        console.log(`❌ No count found for ${statusKey} in variations:`, statusVariations);
        return 0;
    };
    
    // Calculate statistics with case-insensitive matching
    const stats = {
        'total-orders': orders.total_orders || 0,
        'unpicked-count': getStatusCount('unpicked'),
        'picked-count': getStatusCount('picked'),
        'delivered-count': getStatusCount('delivered'),
        'delayed-count': getStatusCount('delayed')
    };
    
    // Also handle "out for delivery" status (count as picked)
    const outForDeliveryCount = getStatusCount('out for delivery');
    if (outForDeliveryCount > 0) {
        stats['picked-count'] += outForDeliveryCount;
        console.log(`📦 Adding ${outForDeliveryCount} "out for delivery" orders to picked count`);
    }

    console.log('📈 Calculated stats:', stats);

    // Update each statistic with animation
    Object.entries(stats).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            const currentValue = parseInt(element.textContent) || 0;
            animateCounter(element, currentValue, value);
            console.log(`✅ Updated ${id}: ${currentValue} → ${value}`);
        } else {
            console.warn(`⚠️ Element not found: ${id}`);
        }
    });

    // Update status overview with delivery and picking data
    const statusData = {
        active_pickers: data.picking?.active_pickers || 0,
        available_pickers: data.picking?.available_pickers || 5,
        active_delivery_boys: data.delivery?.data?.busy_agents?.length || 0,
        available_delivery_boys: data.delivery?.data?.available_agents?.length || 0
    };
    
    updateStatusOverview(statusData);
}

// Animate counter with smooth transitions
function animateCounter(element, start, end) {
    const duration = 1000;
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

// Update status overview with enhanced styling
function updateStatusOverview(data) {
    const activePickers = document.getElementById('active-pickers');
    const availablePickers = document.getElementById('available-pickers');
    const activeDeliveryBoys = document.getElementById('active-delivery-boys');
    const availableDeliveryBoys = document.getElementById('available-delivery-boys');

    if (activePickers) animateCounter(activePickers, 0, data.active_pickers || 0);
    if (availablePickers) animateCounter(availablePickers, 0, data.available_pickers || 5);
    if (activeDeliveryBoys) animateCounter(activeDeliveryBoys, 0, data.active_delivery_boys || 0);
    if (availableDeliveryBoys) animateCounter(availableDeliveryBoys, 0, data.available_delivery_boys || 5);
}

// Enhanced loading states
function showLoading(message = 'Loading...') {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">${message}</p>
        </div>
    `;
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Enhanced notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show notification`;
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    switch(type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-triangle';
        case 'warning': return 'exclamation-triangle';
        case 'info': return 'info-circle';
        default: return 'info-circle';
    }
}

// Auto-refresh functionality
function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(() => {
        if (currentTab === 'dashboard') {
            loadDashboardData();
        }
    }, 30000); // Refresh every 30 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Enhanced refresh function
function refreshDashboard() {
    loadDashboardData();
    showNotification('Dashboard refreshed', 'success');
}

// Fullscreen functionality
function toggleFullscreen() {
    const trackingTab = document.getElementById('tracking-tab');
    
    if (!isFullscreen) {
        trackingTab.classList.add('fullscreen');
        document.body.style.overflow = 'hidden';
        isFullscreen = true;
        showNotification('Entered fullscreen mode', 'info');
    } else {
        trackingTab.classList.remove('fullscreen');
        document.body.style.overflow = '';
        isFullscreen = false;
        showNotification('Exited fullscreen mode', 'info');
    }
}

// Export functionality
function exportTrackingData() {
    if (typeof trackingDashboard !== 'undefined' && trackingDashboard.agentData) {
        const data = {
            timestamp: new Date().toISOString(),
            agents: trackingDashboard.agentData,
            simulation_active: trackingDashboard.isSimulationActive
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tracking-data-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('Tracking data exported successfully', 'success');
    } else {
        showNotification('No tracking data available to export', 'warning');
    }
}

// Enhanced orders data loading
async function loadOrdersData() {
    try {
        showLoading('Loading orders data...');
        
        const response = await fetch('http://127.0.0.1:5000/api/orders');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        if (data.success) {
            updateOrdersTable(data.orders);
            showNotification('Orders data loaded successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to load orders data');
        }
    } catch (error) {
        console.error('Error loading orders data:', error);
        showNotification('Error loading orders data: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Update orders table with enhanced styling
function updateOrdersTable(orders) {
    const activeOrdersBody = document.getElementById('active-orders');
    const completedOrdersBody = document.getElementById('completed-orders');

    if (activeOrdersBody) {
        activeOrdersBody.innerHTML = '';
        orders.filter(order => order.status !== 'delivered').forEach(order => {
            const row = createOrderRow(order);
            activeOrdersBody.appendChild(row);
        });
    }

    if (completedOrdersBody) {
        completedOrdersBody.innerHTML = '';
        orders.filter(order => order.status === 'delivered').forEach(order => {
            const row = createOrderRow(order, true);
            completedOrdersBody.appendChild(row);
        });
    }
}

// Create enhanced order row
function createOrderRow(order, isCompleted = false) {
    const row = document.createElement('tr');
    row.className = 'order-row';
    row.setAttribute('data-order-id', order.id);
    
    const statusClass = getStatusClass(order.status);
    const statusIcon = getStatusIcon(order.status);
    
    row.innerHTML = `
        <td><strong>${order.id}</strong></td>
        <td>${order.items || 'N/A'}</td>
        <td>${order.location || 'N/A'}</td>
        <td>
            <span class="badge ${statusClass}">
                <i class="fas ${statusIcon} me-1"></i>
                ${order.status}
            </span>
        </td>
        <td>
            <span class="badge ${getSlaClass(order.sla)}">
                ${order.sla || 'N/A'}
            </span>
        </td>
        ${!isCompleted ? `
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="trackOrder('${order.id}')">
                <i class="fas fa-map-marker-alt"></i> Track
            </button>
        </td>
        ` : `
        <td>${order.delivered_at || 'N/A'}</td>
        `}
    `;
    
    return row;
}

// Status utility functions
function getStatusClass(status) {
    switch(status) {
        case 'pending': return 'bg-warning';
        case 'picked': return 'bg-info';
        case 'in_transit': return 'bg-primary';
        case 'delivered': return 'bg-success';
        case 'delayed': return 'bg-danger';
        default: return 'bg-secondary';
    }
}

function getStatusIcon(status) {
    switch(status) {
        case 'pending': return 'fa-clock';
        case 'picked': return 'fa-shopping-cart';
        case 'in_transit': return 'fa-truck';
        case 'delivered': return 'fa-check-circle';
        case 'delayed': return 'fa-exclamation-triangle';
        default: return 'fa-question-circle';
    }
}

function getSlaClass(sla) {
    if (!sla) return 'bg-secondary';
    if (sla.includes('On Time')) return 'bg-success';
    if (sla.includes('Delayed')) return 'bg-danger';
    return 'bg-warning';
}

// Track specific order
function trackOrder(orderId) {
    if (typeof trackingDashboard !== 'undefined') {
        switchTab('tracking');
        setTimeout(() => {
            trackingDashboard.trackOrder(orderId);
        }, 500);
    } else {
        showNotification('Tracking dashboard not available', 'error');
    }
}

// Enhanced keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + R to refresh
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        if (currentTab === 'dashboard') {
            refreshDashboard();
        }
    }
    
    // Escape to exit fullscreen
    if (event.key === 'Escape' && isFullscreen) {
        toggleFullscreen();
    }
    
    // Number keys for quick tab switching
    if (event.key >= '1' && event.key <= '5') {
        const tabs = ['dashboard', 'orders', 'picking', 'delivery', 'tracking'];
        const tabIndex = parseInt(event.key) - 1;
        if (tabs[tabIndex]) {
            switchTab(tabs[tabIndex]);
        }
    }
});

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Dark Store Dashboard...');
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        .fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fullscreen {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 9999 !important;
            background: var(--dark-bg) !important;
            padding: 2rem !important;
        }
        
        .order-row {
            transition: all 0.3s ease;
        }
        
        .order-row:hover {
            background: rgba(99, 102, 241, 0.1) !important;
            transform: scale(1.01);
        }
    `;
    document.head.appendChild(style);
    
    // Initialize all dashboard components
    initializeAllComponents();
    
    // Initialize dashboard
    switchTab('dashboard');
    
    console.log('✅ Dashboard initialized successfully');
});

// Initialize all dashboard components
function initializeAllComponents() {
    console.log('🔧 Initializing all dashboard components...');
    
    // Check if all required scripts are loaded
    console.log('📋 Checking script availability:');
    console.log('  - window.initializePickingDashboard:', typeof window.initializePickingDashboard);
    console.log('  - window.initializeDeliveryDashboard:', typeof window.initializeDeliveryDashboard);
    console.log('  - window.trackingDashboard:', typeof window.trackingDashboard);
    console.log('  - window.pickingManager:', typeof window.pickingManager);
    console.log('  - window.deliveryDashboard:', typeof window.deliveryDashboard);
    
    // Initialize picking dashboard
    if (typeof window.initializePickingDashboard === 'function') {
        console.log('🛒 Initializing picking dashboard...');
        try {
            window.initializePickingDashboard();
            console.log('✅ Picking dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing picking dashboard:', error);
        }
    } else {
        console.warn('⚠️ Picking dashboard initialization function not found');
    }
    
    // Initialize delivery dashboard
    if (typeof window.initializeDeliveryDashboard === 'function') {
        console.log('🚚 Initializing delivery dashboard...');
        try {
            window.initializeDeliveryDashboard();
            console.log('✅ Delivery dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing delivery dashboard:', error);
        }
    } else {
        console.warn('⚠️ Delivery dashboard initialization function not found');
    }
    
    // Initialize tracking dashboard (already handled in tracking-dashboard.js)
    if (typeof window.trackingDashboard !== 'undefined') {
        console.log('🗺️ Tracking dashboard already initialized');
    } else {
        console.warn('⚠️ Tracking dashboard not found');
    }
    
    console.log('✅ All components initialized');
}

// Debug functions
window.debugDashboardData = function() {
    console.log('🔍 DEBUGGING DASHBOARD DATA');
    console.log('=' * 50);
    
    // Check current element values
    const elements = ['total-orders', 'unpicked-count', 'picked-count', 'delivered-count', 'delayed-count'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            console.log(`${id}: ${element.textContent}`);
        } else {
            console.log(`${id}: Element not found`);
        }
    });
    
    // Test API call
    testApiEndpoint();
};

window.testApiEndpoint = async function() {
    console.log('🧪 TESTING API ENDPOINT');
    console.log('=' * 50);
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/dashboard');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📡 API Response:', data);
        
        if (data.success) {
            console.log('✅ API call successful');
            console.log('📊 Orders data:', data.orders);
            console.log('📊 Orders by status:', data.orders?.orders_by_status);
            
            // Show notification with summary
            const orders = data.orders || {};
            const status = orders.orders_by_status || {};
            showNotification(`API Test: ${orders.total_orders || 0} total orders, ${status.Picked || status.picked || 0} picked`, 'info');
        } else {
            console.error('❌ API call failed:', data.error);
            showNotification('API test failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('❌ API test error:', error);
        showNotification('API test error: ' + error.message, 'error');
    }
};

// Enhanced error handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showNotification('An error occurred. Please refresh the page.', 'error');
});

// Enhanced unload handling
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});