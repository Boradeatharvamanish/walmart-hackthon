// delivery-dashboard.js - Separate delivery dashboard functionality
console.log('🚚 Loading Delivery Dashboard...');

// Delivery Dashboard Class
class DeliveryDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.deliveryBoys = [];
        this.assignments = {};
        this.readyOrders = [];
        this.refreshInterval = null;
        this.isLoading = false;
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing Delivery Dashboard...');
        this.setupEventListeners();
        this.startAutoRefresh();
        // Initial data load
        this.refreshDeliveryData();
    }

    setupEventListeners() {
        // Auto-refresh when tab becomes active
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isCurrentTab('delivery')) {
                this.refreshDeliveryData();
            }
        });

        // Setup the assign delivery button
        const assignBtn = document.getElementById('assign-delivery-btn');
        if (assignBtn) {
            assignBtn.addEventListener('click', () => {
                console.log('🔄 Assign button clicked');
                this.assignDeliveryOrders();
            });
        } else {
            console.warn('⚠️ Assign delivery button not found');
        }
    }

    isCurrentTab(tabName) {
        const tab = document.getElementById(`${tabName}-tab`);
        return tab && tab.style.display !== 'none';
    }

    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.isCurrentTab('delivery')) {
                this.refreshDeliveryData();
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showLoading() {
        this.isLoading = true;
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        this.isLoading = false;
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showToast(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        
        const toast = document.getElementById('notification-toast');
        const toastBody = document.getElementById('toast-message');
        
        if (toast && toastBody) {
            toastBody.textContent = message;
            toast.className = `toast ${type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-info'}`;
            
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                const bsToast = new bootstrap.Toast(toast);
                bsToast.show();
            }
        } else {
            // Fallback alert
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }

    async makeApiCall(endpoint, options = {}) {
        try {
            console.log(`🔄 Making API call to: ${this.apiBaseUrl}${endpoint}`);
            
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            console.log(`📡 API Response Status: ${response.status}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ API Response Data:`, data);
            return data;
        } catch (error) {
            console.error(`❌ API call failed for ${endpoint}:`, error);
            throw error;
        }
    }

    async refreshDeliveryData() {
        if (this.isLoading) return;

        try {
            console.log('🔄 Refreshing delivery data...');
            
            // Fetch all delivery-related data
            const [statusResponse, assignmentsResponse, ordersResponse] = await Promise.all([
                this.makeApiCall('/delivery/status'),
                this.makeApiCall('/delivery/assignments'),
                this.makeApiCall('/delivery/available-orders')
            ]);

            console.log('📊 API Responses:', {
                status: statusResponse,
                assignments: assignmentsResponse,
                orders: ordersResponse
            });

            if (statusResponse.success) {
                this.deliveryBoys = statusResponse.delivery_boys || {};
                this.updateDeliveryBoysGrid();
            }

            if (assignmentsResponse.success) {
                this.assignments = assignmentsResponse.assignments || {};
                this.updateAssignmentsView();
            }

            if (ordersResponse.success) {
                this.readyOrders = ordersResponse.available_orders || [];
                this.updateReadyOrdersTable();
            }

        } catch (error) {
            console.error('❌ Error refreshing delivery data:', error);
            this.showToast('Failed to refresh delivery data. Check console for details.', 'error');
        }
    }

    updateDeliveryBoysGrid() {
        const container = document.getElementById('delivery-boys-grid');
        if (!container) {
            console.warn('⚠️ delivery-boys-grid element not found');
            return;
        }

        console.log('🔄 Updating delivery boys grid...', this.deliveryBoys);

        const deliveryBoysArray = Object.values(this.deliveryBoys);
        
        if (deliveryBoysArray.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h4>No Delivery Boys Available</h4>
                    <p>No delivery boys are currently configured in the system.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = deliveryBoysArray.map(boy => {
            const isAvailable = boy.assigned_orders.length === 0;
            const statusClass = isAvailable ? 'available' : 'busy';
            const statusText = isAvailable ? 'Available' : 'Busy';

            return `
                <div class="delivery-boy-card ${statusClass} fade-in">
                    <div class="delivery-boy-header">
                        <div>
                            <h5 class="delivery-boy-name">${boy.name}</h5>
                            <p class="delivery-boy-id">${boy.id}</p>
                        </div>
                        <div class="delivery-boy-status ${statusClass}">
                            ${statusText}
                        </div>
                    </div>
                    <div class="delivery-boy-orders">
                        <h6>Assigned Orders</h6>
                        <div class="order-count">${boy.assigned_orders.length}</div>
                        ${boy.assigned_orders.length > 0 ? 
                            `<div class="order-list">
                                ${boy.assigned_orders.slice(0, 3).map(orderId => 
                                    `<div class="order-tag">${orderId}</div>`
                                ).join('')}
                                ${boy.assigned_orders.length > 3 ? 
                                    `<div class="order-tag">+${boy.assigned_orders.length - 3} more</div>` : ''
                                }
                            </div>` : ''
                        }
                    </div>
                </div>
            `;
        }).join('');
    }

    updateAssignmentsView() {
        const container = document.getElementById('delivery-assignments-row');
        if (!container) {
            console.warn('⚠️ delivery-assignments-row element not found');
            return;
        }

        console.log('🔄 Updating assignments view...', this.assignments);

        const assignmentsArray = Object.entries(this.assignments);
        
        if (assignmentsArray.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="empty-state">
                        <h4>No Active Assignments</h4>
                        <p>No orders are currently assigned to delivery boys.</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = assignmentsArray.map(([boyId, assignment]) => {
            const boy = assignment.delivery_boy;
            const orders = assignment.orders || [];
            
            if (orders.length === 0) return '';

            const totalAmount = orders.reduce((sum, order) => sum + (order.total_amount || 0), 0);

            return `
                <div class="col-lg-6 col-md-12 mb-4">
                    <div class="assignment-card fade-in">
                        <div class="assignment-header">
                            <div class="assignment-boy-info">
                                <h5>${boy.name}</h5>
                                <p>${boy.id}</p>
                            </div>
                            <div class="assignment-stats">
                                <div class="stat-item">
                                    <div class="stat-value">${orders.length}</div>
                                    <div class="stat-label">Orders</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">₹${totalAmount}</div>
                                    <div class="stat-label">Total</div>
                                </div>
                            </div>
                        </div>
                        <div class="orders-list">
                            ${orders.map(order => `
                                <div class="order-item ${order.batched_with ? 'batched' : 'primary'}">
                                    <div class="order-header">
                                        <div class="order-id">${order.order_id}</div>
                                        <div class="order-type ${order.batched_with ? 'batched' : 'primary'}">
                                            ${order.batched_with ? 'Batched' : 'Primary'}
                                        </div>
                                    </div>
                                    <div class="order-details">
                                        <p><strong>Customer:</strong> ${order.customer_name || 'N/A'}</p>
                                        <p><strong>Address:</strong> ${order.delivery_address || 'N/A'}</p>
                                        <p><strong>Amount:</strong> ₹${order.total_amount || 0}</p>
                                        ${order.distance_from_primary ? 
                                            `<p><strong>Distance:</strong> <span class="distance-badge">${order.distance_from_primary} km</span></p>` 
                                            : ''
                                        }
                                    </div>
                                    <div class="order-actions">
                                        <button class="btn btn-sm btn-success" onclick="window.deliveryDashboard.updateDeliveryStatus('${order.order_id}', 'delivered')">
                                            Mark Delivered
                                        </button>
                                        <button class="btn btn-sm btn-warning" onclick="window.deliveryDashboard.updateDeliveryStatus('${order.order_id}', 'failed')">
                                            Mark Failed
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateReadyOrdersTable() {
        const tbody = document.getElementById('ready-orders-table');
        if (!tbody) {
            console.warn('⚠️ ready-orders-table element not found');
            return;
        }

        console.log('🔄 Updating ready orders table...', this.readyOrders);

        if (this.readyOrders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">
                        <div class="empty-state">
                            <h6>No Orders Ready for Delivery</h6>
                            <p>All picked orders have been assigned to delivery boys.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.readyOrders.map(order => `
            <tr>
                <td>${order.order_id}</td>
                <td>${order.customer_name || 'N/A'}</td>
                <td>${order.delivery_address || 'N/A'}</td>
                <td>
                    <span class="status-badge ${order.current_status?.toLowerCase() || 'unknown'}">
                        ${order.current_status || 'Unknown'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="window.deliveryDashboard.assignSingleOrder('${order.order_id}')">
                        Assign
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async assignDeliveryOrders() {
        if (this.isLoading) return;

        try {
            console.log('🚀 Starting delivery assignment...');
            this.showLoading();
            
            const maxDistance = document.getElementById('max-distance')?.value || 1.0;
            
            const response = await this.makeApiCall('/delivery/assign', {
                method: 'POST',
                body: JSON.stringify({
                    max_distance_km: parseFloat(maxDistance)
                })
            });

            console.log('📊 Assignment response:', response);

            if (response.success) {
                this.showToast(
                    `Successfully assigned ${response.total_orders_assigned || 0} orders to delivery boys`, 
                    'success'
                );
                await this.refreshDeliveryData();
            } else {
                this.showToast(response.error || response.message || 'Failed to assign orders', 'error');
            }

        } catch (error) {
            console.error('❌ Error assigning delivery orders:', error);
            this.showToast('Failed to assign delivery orders. Check console for details.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async assignSingleOrder(orderId) {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const response = await this.makeApiCall('/delivery/assign-single', {
                method: 'POST',
                body: JSON.stringify({
                    order_id: orderId
                })
            });

            if (response.success) {
                this.showToast(`Order ${orderId} assigned successfully`, 'success');
                await this.refreshDeliveryData();
            } else {
                this.showToast(response.error || response.message || 'Failed to assign order', 'error');
            }

        } catch (error) {
            console.error('❌ Error assigning single order:', error);
            this.showToast('Failed to assign order', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async resetDeliveryAssignments() {
        if (this.isLoading) return;

        if (!confirm('Are you sure you want to reset all delivery assignments? This will unassign all orders from delivery boys.')) {
            return;
        }

        try {
            this.showLoading();
            
            const response = await this.makeApiCall('/delivery/reset', {
                method: 'POST'
            });

            if (response.success) {
                this.showToast('All delivery assignments have been reset', 'success');
                await this.refreshDeliveryData();
            } else {
                this.showToast(response.error || response.message || 'Failed to reset assignments', 'error');
            }

        } catch (error) {
            console.error('❌ Error resetting delivery assignments:', error);
            this.showToast('Failed to reset delivery assignments', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async updateDeliveryStatus(orderId, status) {
        if (this.isLoading) return;

        try {
            const response = await this.makeApiCall('/delivery/update-status', {
                method: 'POST',
                body: JSON.stringify({
                    order_id: orderId,
                    status: status
                })
            });

            if (response.success) {
                this.showToast(`Order ${orderId} status updated to ${status}`, 'success');
                await this.refreshDeliveryData();
            } else {
                this.showToast(response.error || response.message || 'Failed to update status', 'error');
            }

        } catch (error) {
            console.error('❌ Error updating delivery status:', error);
            this.showToast('Failed to update delivery status', 'error');
        }
    }

    async refreshDeliveryAgents() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const response = await this.makeApiCall('/delivery/refresh', {
                method: 'POST'
            });

            if (response.success) {
                this.showToast('Delivery agents refreshed successfully', 'success');
                await this.refreshDeliveryData();
            } else {
                this.showToast(response.error || response.message || 'Failed to refresh agents', 'error');
            }

        } catch (error) {
            console.error('❌ Error refreshing delivery agents:', error);
            this.showToast('Failed to refresh delivery agents', 'error');
        } finally {
            this.hideLoading();
        }
    }

    destroy() {
        this.stopAutoRefresh();
        console.log('🔄 Delivery Dashboard destroyed');
    }
}

// Global functions for delivery dashboard
window.assignDeliveryOrders = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.assignDeliveryOrders();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.resetDeliveryAssignments = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.resetDeliveryAssignments();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.refreshDeliveryData = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.refreshDeliveryData();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.assignSingleOrder = function(orderId) {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.assignSingleOrder(orderId);
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.updateDeliveryStatus = function(orderId, status) {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.updateDeliveryStatus(orderId, status);
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.refreshDeliveryAgents = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.refreshDeliveryAgents();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

// Initialize delivery dashboard when delivery tab is accessed
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚚 Delivery Dashboard JS loaded');
    
    // Test API connectivity
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('🔄 Testing API connectivity...');
        fetch('http://localhost:5000/health')
            .then(response => response.json())
            .then(data => {
                console.log('✅ API Health Check:', data);
            })
            .catch(error => {
                console.error('❌ API Health Check Failed:', error);
                console.log('💡 Make sure your Flask server is running on port 5000');
            });
    }
});

// Enhanced tab switching to initialize delivery dashboard
function initializeDeliveryDashboard() {
    if (!window.deliveryDashboard) {
        console.log('🚀 Initializing delivery dashboard...');
        window.deliveryDashboard = new DeliveryDashboard();
    } else {
        console.log('🔄 Refreshing existing delivery dashboard...');
        window.deliveryDashboard.refreshDeliveryData();
    }
}

// Export for use in main dashboard
window.initializeDeliveryDashboard = initializeDeliveryDashboard;

console.log('✅ Delivery Dashboard JS loaded successfully');