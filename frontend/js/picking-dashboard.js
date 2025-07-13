// Enhanced Picking Dashboard Logic
class PickingManager {
  constructor() {
    this.apiBaseUrl = 'http://localhost:5000/api';
    this.allOrders = {};
    this.activeOrders = [];
    this.queuedOrders = [];
    this.pickers = [
      { id: 1, name: "Alex Kumar", active: false, orderId: null, progress: 0, order_details: {} },
      { id: 2, name: "Priya Sharma", active: false, orderId: null, progress: 0, order_details: {} },
      { id: 3, name: "Raj Patel", active: false, orderId: null, progress: 0, order_details: {} },
      { id: 4, name: "Sarah Khan", active: false, orderId: null, progress: 0, order_details: {} },
      { id: 5, name: "Mike Johnson", active: false, orderId: null, progress: 0, order_details: {} }
    ];
    this.refreshInterval = null;
    this.progressSimulationInterval = null;
    this.initializeDashboard();
  }

  initializeDashboard() {
    console.log('🛒 Initializing Picking Dashboard...');
    this.loadPickingData();
    this.startAutoRefresh();
    this.startProgressSimulation();
    this.setupGlobalButtonHandlers();
  }

  startAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    this.refreshInterval = setInterval(() => {
      if (this.isCurrentTab('picking')) {
        this.loadPickingData();
      }
    }, 5000); // Refresh every 5 seconds
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  isCurrentTab(tabName) {
    const tab = document.getElementById(`${tabName}-tab`);
    return tab && tab.style.display !== 'none';
  }

  async loadPickingData() {
    try {
      console.log('🔄 Loading picking data from API...');
      
      // First, try to auto-assign orders to pickers
      await this.autoAssignOrders();
      
      // Then load the current picking status
      const response = await fetch(`${this.apiBaseUrl}/picking/status`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error Response: ${errorText}`);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();

      if (data.success !== false) {
        this.updatePickersFromBackend(data.pickers || []);
        console.log('✅ Picking data loaded successfully');
      } else {
        console.error('❌ Failed to load picking data:', data.error);
      }
    } catch (error) {
      console.error('❌ Failed to load picking data:', error.message);
    }
  }

  updatePickersFromBackend(backendPickers) {
    // Update local pickers with backend data
    this.pickers.forEach(picker => {
      const backendPicker = backendPickers.find(p => p.id === picker.id);
      if (backendPicker) {
        picker.active = backendPicker.active || false;
        picker.orderId = backendPicker.order_id || null;
        picker.progress = backendPicker.progress || 0;
        picker.order_details = backendPicker.order_details || {};
      } else {
        // Reset picker if not found in backend
        picker.active = false;
        picker.orderId = null;
        picker.progress = 0;
        picker.order_details = {};
      }
    });
    
    this.renderPickingDashboard();
  }

  async autoAssignOrders() {
    try {
      console.log('🔄 Auto-assigning orders to pickers...');
      
      const response = await fetch(`${this.apiBaseUrl}/picking/auto-assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log(`✅ Auto-assigned ${data.assigned_count} orders to pickers`);
          if (data.failed_assignments && data.failed_assignments.length > 0) {
            console.warn(`⚠️ ${data.failed_count} assignments failed:`, data.failed_assignments);
          }
        } else {
          console.warn('⚠️ Auto-assignment failed:', data.message);
        }
      } else {
        console.error('❌ Auto-assignment API error:', response.status);
      }
    } catch (error) {
      console.error('❌ Error in auto-assignment:', error);
    }
  }

  renderPickingDashboard() {
    this.renderActivePicks();
    this.renderQueue();
    this.updateStatistics();
  }

  renderActivePicks() {
    const container = document.getElementById('active-picks-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    this.pickers.forEach(picker => {
      const card = document.createElement('div');
      card.className = 'picking-card';
      
      if (picker.active && picker.orderId) {
        const order = picker.order_details || {};
        card.innerHTML = `
          <div class="picker-header">
            <div class="picker-info">
              <span class="picker-name">👤 ${picker.name}</span>
              <span class="picker-status active">🟢 Active</span>
            </div>
          </div>
          <div class="order-info">
            <h4>📦 ${picker.orderId}</h4>
            <div class="order-items">
              <strong>Items:</strong> ${(order.order_items || []).join(', ')}
            </div>
            <div class="order-location">
              <strong>Location:</strong> ${order.delivery_location ? `${order.delivery_location.lat?.toFixed(3)}, ${order.delivery_location.lng?.toFixed(3)}` : 'N/A'}
            </div>
          </div>
          <div class="progress-section">
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${picker.progress}%"></div>
            </div>
            <span class="progress-text">${picker.progress}% Complete</span>
          </div>
          <div class="picking-actions">
            <button class="btn btn-sm btn-success" onclick="pickingManager.completeOrder('${picker.orderId}', ${picker.id})" ${picker.progress < 100 ? 'disabled' : ''}>
              ✅ Mark Complete
            </button>
            <button class="btn btn-sm btn-warning" onclick="pickingManager.updateProgress(${picker.id}, ${Math.min(picker.progress + 10, 100)})">
              ⚡ +10% Progress
            </button>
          </div>
        `;
      } else {
        card.innerHTML = `
          <div class="picker-header">
            <div class="picker-info">
              <span class="picker-name">👤 ${picker.name}</span>
              <span class="picker-status inactive">⚪ Available</span>
            </div>
          </div>
          <div class="order-info">
            <h4>📦 No Order Assigned</h4>
            <div class="order-items">
              <em>Waiting for assignment...</em>
            </div>
          </div>
          <div class="progress-section">
            <div class="progress-bar">
              <div class="progress-fill" style="width: 0%"></div>
            </div>
            <span class="progress-text">0% Complete</span>
          </div>
          <div class="picking-actions">
            <button class="btn btn-sm btn-secondary" disabled>
              ⏳ Waiting
            </button>
          </div>
        `;
      }
      
      container.appendChild(card);
    });
  }

  renderQueue() {
    const container = document.getElementById('queue-container');
    if (!container) return;
    
    // Get unpicked orders from backend
    this.loadUnpickedOrders().then(unpickedOrders => {
      const queueOrders = unpickedOrders.filter(order => {
        // Filter out orders that are already assigned to pickers
        return !this.pickers.some(picker => 
          picker.active && picker.orderId === order.order_id
        );
      });
      
      container.innerHTML = '';
      
      if (queueOrders.length === 0) {
        container.innerHTML = '<div class="queue-empty">📦 No orders in queue</div>';
        return;
      }
      
      queueOrders.forEach(order => {
        const orderCard = document.createElement('div');
        orderCard.className = 'queue-order-card';
        orderCard.innerHTML = `
          <div class="order-header">
            <h5>📦 ${order.order_id}</h5>
            <span class="order-status unpicked">⏳ Unpicked</span>
          </div>
          <div class="order-details">
            <div class="order-items">
              <strong>Items:</strong> ${(order.order_items || []).join(', ')}
            </div>
            <div class="order-location">
              <strong>Location:</strong> ${order.delivery_location ? `${order.delivery_location.lat?.toFixed(3)}, ${order.delivery_location.lng?.toFixed(3)}` : 'N/A'}
            </div>
          </div>
        `;
        container.appendChild(orderCard);
      });
    });
  }

  async loadUnpickedOrders() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/picking/available-orders`);
      if (response.ok) {
        const data = await response.json();
        return data.available_orders || [];
      }
    } catch (error) {
      console.error('❌ Error loading unpicked orders:', error);
    }
    return [];
  }

  updateStatistics() {
    const activePickers = this.pickers.filter(p => p.active).length;
    const availablePickers = this.pickers.filter(p => !p.active).length;
    const totalOrders = this.pickers.filter(p => p.active && p.orderId).length;
    
    // Update stats display
    const statsContainer = document.getElementById('picking-stats');
    if (statsContainer) {
      statsContainer.innerHTML = `
        <div class="stat-item">
          <span class="stat-label">Active Pickers:</span>
          <span class="stat-value">${activePickers}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Available Pickers:</span>
          <span class="stat-value">${availablePickers}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Orders in Progress:</span>
          <span class="stat-value">${totalOrders}</span>
        </div>
      `;
    }
  }

  async completeOrder(orderId, pickerId) {
    try {
      console.log(`✅ Completing order ${orderId} for picker ${pickerId}`);
      
      const response = await fetch(`${this.apiBaseUrl}/picking/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          picker_id: pickerId
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          this.showNotification(`✅ Order ${orderId} completed successfully!`, 'success');
          this.loadPickingData(); // Refresh data
        } else {
          this.showNotification(`❌ Failed to complete order: ${data.message}`, 'error');
        }
      } else {
        this.showNotification(`❌ Error completing order: ${response.status}`, 'error');
      }
    } catch (error) {
      console.error('❌ Error completing order:', error);
      this.showNotification(`❌ Error completing order: ${error.message}`, 'error');
    }
  }

  async updateProgress(pickerId, newProgress) {
    try {
      console.log(`⚡ Updating progress for picker ${pickerId} to ${newProgress}%`);
      
      const response = await fetch(`${this.apiBaseUrl}/picking/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          picker_id: pickerId,
          progress: newProgress
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          this.showNotification(`⚡ Progress updated to ${newProgress}%`, 'info');
          this.loadPickingData(); // Refresh data
        } else {
          this.showNotification(`❌ Failed to update progress: ${data.message}`, 'error');
        }
      } else {
        this.showNotification(`❌ Error updating progress: ${response.status}`, 'error');
      }
    } catch (error) {
      console.error('❌ Error updating progress:', error);
      this.showNotification(`❌ Error updating progress: ${error.message}`, 'error');
    }
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  async resetAllPickers() {
    try {
      console.log('🔄 Resetting all pickers...');
      
      const response = await fetch(`${this.apiBaseUrl}/picking/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          this.showNotification('✅ All pickers reset successfully!', 'success');
          this.loadPickingData(); // Refresh data
        } else {
          this.showNotification(`❌ Failed to reset pickers: ${data.message}`, 'error');
        }
      } else {
        this.showNotification(`❌ Error resetting pickers: ${response.status}`, 'error');
      }
    } catch (error) {
      console.error('❌ Error resetting pickers:', error);
      this.showNotification(`❌ Error resetting pickers: ${error.message}`, 'error');
    }
  }

  setupGlobalButtonHandlers() {
    // Global button handlers for picking dashboard
    window.resetAllPickers = () => this.resetAllPickers();
    window.autoAssignOrders = () => this.autoAssignOrders();
  }

  startProgressSimulation() {
    // Simulate progress updates for active pickers
    this.progressSimulationInterval = setInterval(() => {
      this.pickers.forEach(picker => {
        if (picker.active && picker.progress < 100) {
          // Simulate natural progress increase
          const increment = Math.random() * 5; // 0-5% random increment
          const newProgress = Math.min(picker.progress + increment, 100);
          
          if (newProgress !== picker.progress) {
            this.updateProgress(picker.id, newProgress);
          }
        }
      });
    }, 10000); // Update every 10 seconds
  }

  stopProgressSimulation() {
    if (this.progressSimulationInterval) {
      clearInterval(this.progressSimulationInterval);
      this.progressSimulationInterval = null;
    }
  }

  destroy() {
    this.stopAutoRefresh();
    this.stopProgressSimulation();
  }
}

// Initialize picking manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.pickingManager = new PickingManager();
});