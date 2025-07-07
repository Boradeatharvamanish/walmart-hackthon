// delivery-dashboard.js - Updated to match backend API endpoints
console.log('🚚 Loading Delivery Dashboard...');

// Delivery Dashboard Class
class DeliveryDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.deliveryBoys = [];
        this.readyOrders = [];
        this.refreshInterval = null;
        this.isLoading = false;
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing Delivery Dashboard...');
        this.startAutoRefresh();
        // Initial data load
        this.refreshDeliveryData();
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
            
            // Fetch delivery status and picked orders using correct API endpoints
            const [deliveryStatusResponse, pickedOrdersResponse] = await Promise.all([
                this.makeApiCall('/delivery/status'),
                this.makeApiCall('/delivery/picked-orders')
            ]);

            console.log('📊 API Responses:', {
                deliveryStatus: deliveryStatusResponse,
                pickedOrders: pickedOrdersResponse
            });

            if (deliveryStatusResponse.success) {
                // Combine available and busy agents
                const availableAgents = deliveryStatusResponse.data.available_agents || [];
                const busyAgents = deliveryStatusResponse.data.busy_agents || [];
                this.deliveryBoys = [...availableAgents, ...busyAgents];
                this.updateDeliveryBoysGrid();
            }

            if (pickedOrdersResponse.success) {
                this.readyOrders = pickedOrdersResponse.data.picked_orders || [];
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

        if (this.deliveryBoys.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h4>No Delivery Boys Available</h4>
                    <p>No delivery boys are currently configured in the system.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.deliveryBoys.map(deliveryBoy => {
            const isAvailable = deliveryBoy.status === 'available';
            const statusClass = isAvailable ? 'available' : 'busy';
            const statusText = isAvailable ? 'Available' : 'Busy';
            const currentOrdersCount = deliveryBoy.order_assigned ? deliveryBoy.order_assigned.length : 0;

            return `
                <div class="delivery-boy-card ${statusClass} fade-in">
                    <div class="delivery-boy-header">
                        <div class="delivery-boy-avatar">
                            <div class="avatar-circle ${statusClass}">
                                ${deliveryBoy.name ? deliveryBoy.name.charAt(0).toUpperCase() : 'D'}
                            </div>
                        </div>
                        <div class="delivery-boy-info">
                            <h5 class="delivery-boy-name">${deliveryBoy.name || 'Unknown'}</h5>
                            <p class="delivery-boy-id">ID: ${deliveryBoy.id || 'N/A'}</p>
                            <p class="delivery-boy-phone">📞 ${deliveryBoy.phone || 'N/A'}</p>
                        </div>
                        <div class="delivery-boy-status ${statusClass}">
                            <span class="status-dot"></span>
                            ${statusText}
                        </div>
                    </div>
                    
                    <div class="delivery-boy-stats">
                        <div class="stat-item">
                            <span class="stat-label">Assigned Orders</span>
                            <span class="stat-value">${currentOrdersCount}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Location</span>
                            <span class="stat-value">${deliveryBoy.current_location ? 'Available' : 'Unknown'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Status</span>
                            <span class="stat-value">${deliveryBoy.status || 'N/A'}</span>
                        </div>
                    </div>

                    <div class="delivery-boy-location">
                        <p class="location-text">📍 ${deliveryBoy.current_location && deliveryBoy.current_location.address ? deliveryBoy.current_location.address : 'Location not available'}</p>
                    </div>

                    ${currentOrdersCount > 0 ? `
                        <div class="delivery-boy-orders">
                            <h6>Assigned Orders</h6>
                            <div class="order-list">
                                ${deliveryBoy.order_assigned.slice(0, 3).map(orderId => 
                                    `<div class="order-tag">${orderId}</div>`
                                ).join('')}
                                ${currentOrdersCount > 3 ? 
                                    `<div class="order-tag">+${currentOrdersCount - 3} more</div>` : ''
                                }
                            </div>
                        </div>
                    ` : ''}

                    <div class="delivery-boy-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="window.deliveryDashboard.viewAgentOrders('${deliveryBoy.id}')">
                            View Orders
                        </button>
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
                            <p>No orders are currently picked and ready for delivery assignment.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.readyOrders.map(order => {
            const itemCount = order.order_items ? order.order_items.length : 0;
            const deliveryAddress = order.delivery_location ? 
                (order.delivery_location.address || 'Address not available') : 'Address not available';
            const currentStatus = order.current_status || 'Picked';

            return `
                <tr>
                    <td>
                        <strong>${order.order_id}</strong>
                        <br>
                        <small class="text-muted">Status: ${currentStatus}</small>
                    </td>
                    <td>
                        <div class="address-info">
                            <strong>${deliveryAddress}</strong>
                            <br>
                            <small class="text-muted">📍 ${order.pincode || 'N/A'}</small>
                        </div>
                    </td>
                    <td>
                        <span class="status-badge ${currentStatus.toLowerCase().replace(/\s+/g, '-')}">
                            ${currentStatus}
                        </span>
                        <br>
                        <small class="text-muted">${itemCount} items</small>
                    </td>
                    <td>
                        <div class="order-actions">
                            <button class="btn btn-sm btn-primary" onclick="window.deliveryDashboard.viewOrderDetails('${order.order_id}')">
                                View Items
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    async viewOrderDetails(orderId) {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            // Find the order in our current data
            const order = this.readyOrders.find(o => o.order_id === orderId);
            
            if (order) {
                this.showOrderDetailsModal(order);
            } else {
                this.showToast('Order not found', 'error');
            }

        } catch (error) {
            console.error('❌ Error getting order details:', error);
            this.showToast('Failed to get order details', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async viewAgentOrders(agentId) {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const response = await this.makeApiCall(`/delivery/agent/${agentId}/orders`);

            if (response.success) {
                this.showAgentOrdersModal(response.data);
            } else {
                this.showToast(response.message || 'Failed to get agent orders', 'error');
            }

        } catch (error) {
            console.error('❌ Error getting agent orders:', error);
            this.showToast('Failed to get agent orders', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showOrderDetailsModal(order) {
        const items = order.order_items || [];
        
        const modalContent = `
            <div class="modal fade" id="orderDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Order Details - ${order.order_id}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="order-info">
                                        <h6>Order Information</h6>
                                        <p><strong>Order ID:</strong> ${order.order_id}</p>
                                        <p><strong>Status:</strong> <span class="badge bg-info">${order.current_status}</span></p>
                                        <p><strong>Total Items:</strong> ${items.length}</p>
                                        <p><strong>Pincode:</strong> ${order.pincode || 'N/A'}</p>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="delivery-info">
                                        <h6>Delivery Information</h6>
                                        <p><strong>Address:</strong> ${order.delivery_location && order.delivery_location.address ? order.delivery_location.address : 'N/A'}</p>
                                        <p><strong>Coordinates:</strong> ${order.delivery_location && order.delivery_location.coordinates ? `${order.delivery_location.coordinates.lat}, ${order.delivery_location.coordinates.lng}` : 'N/A'}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="items-info mt-3">
                                <h6>Order Items</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Item</th>
                                                <th>Quantity</th>
                                                <th>Details</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${items.map(item => `
                                                <tr>
                                                    <td>${item.item_name || item.name || 'Unknown Item'}</td>
                                                    <td>${item.quantity || 1}</td>
                                                    <td>${item.description || 'No description'}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('orderDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalContent);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
        modal.show();
    }

    showAgentOrdersModal(agentData) {
        const modalContent = `
            <div class="modal fade" id="agentOrdersModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Agent Orders - ${agentData.agent_name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="agent-info">
                                        <h6>Agent Information</h6>
                                        <p><strong>Agent ID:</strong> ${agentData.agent_id}</p>
                                        <p><strong>Name:</strong> ${agentData.agent_name}</p>
                                        <p><strong>Status:</strong> <span class="badge ${agentData.status === 'available' ? 'bg-success' : 'bg-warning'}">${agentData.status}</span></p>
                                        <p><strong>Total Orders:</strong> ${agentData.total_orders}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="orders-info mt-3">
                                <h6>Assigned Orders</h6>
                                ${agentData.assigned_orders.length > 0 ? `
                                    <div class="table-responsive">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Order ID</th>
                                                    <th>Status</th>
                                                    <th>Items</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${agentData.orders_info.map(orderInfo => `
                                                    <tr>
                                                        <td>${orderInfo.order_id}</td>
                                                        <td><span class="badge bg-info">${orderInfo.order_data.current_status || 'N/A'}</span></td>
                                                        <td>${orderInfo.order_data.order_items ? orderInfo.order_data.order_items.length : 0} items</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                ` : '<p class="text-muted">No orders assigned to this agent.</p>'}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('agentOrdersModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalContent);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('agentOrdersModal'));
        modal.show();
    }

    // New methods for clustering functionality
    async clusterOrders() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const response = await this.makeApiCall('/delivery/cluster-orders', {
                method: 'POST'
            });

            if (response.success) {
                this.showToast('Orders clustered successfully', 'success');
                this.refreshDeliveryData(); // Refresh the display
            } else {
                this.showToast(response.message || 'Failed to cluster orders', 'error');
            }

        } catch (error) {
            console.error('❌ Error clustering orders:', error);
            this.showToast('Failed to cluster orders', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async assignClusters() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const response = await this.makeApiCall('/delivery/assign-clusters', {
                method: 'POST'
            });

            if (response.success) {
                this.showToast('Clusters assigned successfully', 'success');
                this.refreshDeliveryData(); // Refresh the display
            } else {
                this.showToast(response.message || 'Failed to assign clusters', 'error');
            }

        } catch (error) {
            console.error('❌ Error assigning clusters:', error);
            this.showToast('Failed to assign clusters', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async getClusters() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const response = await this.makeApiCall('/delivery/clusters');

            if (response.success) {
                this.showClustersModal(response.data);
            } else {
                this.showToast(response.message || 'Failed to get clusters', 'error');
            }

        } catch (error) {
            console.error('❌ Error getting clusters:', error);
            this.showToast('Failed to get clusters', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showClustersModal(clustersData) {
        const modalContent = `
            <div class="modal fade" id="clustersModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Delivery Clusters</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="clusters-info">
                                        <h6>Clusters Overview</h6>
                                        <p><strong>Total Clusters:</strong> ${clustersData.total_clusters}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="clusters-details mt-3">
                                <h6>Cluster Details</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Cluster ID</th>
                                                <th>Orders</th>
                                                <th>Agent</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${clustersData.clusters.map((cluster, index) => `
                                                <tr>
                                                    <td>Cluster ${index + 1}</td>
                                                    <td>${cluster.orders ? cluster.orders.length : 0} orders</td>
                                                    <td>${cluster.agent_id || 'Unassigned'}</td>
                                                    <td><span class="badge ${cluster.agent_id ? 'bg-success' : 'bg-warning'}">${cluster.agent_id ? 'Assigned' : 'Pending'}</span></td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('clustersModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalContent);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('clustersModal'));
        modal.show();
    }

    destroy() {
        this.stopAutoRefresh();
        console.log('🔄 Delivery Dashboard destroyed');
    }
}

// Global functions for delivery dashboard
window.refreshDeliveryData = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.refreshDeliveryData();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.viewOrderDetails = function(orderId) {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.viewOrderDetails(orderId);
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.clusterOrders = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.clusterOrders();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.assignClusters = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.assignClusters();
    } else {
        console.error('❌ Delivery dashboard not initialized');
    }
};

window.getClusters = function() {
    if (window.deliveryDashboard) {
        window.deliveryDashboard.getClusters();
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