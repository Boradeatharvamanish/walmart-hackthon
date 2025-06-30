// Picking Dashboard Logic
class PickingManager {
    constructor() {
      this.pickers = [
        { id: 1, name: "Alex Kumar", active: false, orderId: null, progress: 0 },
        { id: 2, name: "Priya Sharma", active: false, orderId: null, progress: 0 },
        { id: 3, name: "Raj Patel", active: false, orderId: null, progress: 0 },
        { id: 4, name: "Sarah Khan", active: false, orderId: null, progress: 0 },
        { id: 5, name: "Mike Johnson", active: false, orderId: null, progress: 0 }
      ];
      
      this.activeOrders = [];
      this.queuedOrders = [];
      this.allOrders = {};
      
      this.progressInterval = null;
    }
  
    initializeDashboard() {
      this.startProgressSimulation();
      this.renderPickingDashboard();
    }
  
    updateOrders(orders) {
      this.allOrders = orders || {};
      
      // Filter unpicked orders
      const unpickedOrders = Object.keys(this.allOrders)
        .filter(key => {
          const order = this.allOrders[key];
          return !order.current_status || order.current_status === "Unpicked";
        })
        .map(key => ({
          id: key,
          ...this.allOrders[key]
        }));
  
      // Assign orders to available pickers
      this.assignOrdersToPickers(unpickedOrders);
      this.renderPickingDashboard();
    }
  
    assignOrdersToPickers(unpickedOrders) {
      // Reset if no unpicked orders
      if (unpickedOrders.length === 0) {
        this.pickers.forEach(picker => {
          picker.active = false;
          picker.orderId = null;
          picker.progress = 0;
        });
        this.activeOrders = [];
        this.queuedOrders = [];
        return;
      }
  
      // Assign orders to inactive pickers
      let orderIndex = 0;
      
      // First, maintain existing active assignments
      this.pickers.forEach(picker => {
        if (picker.active && picker.orderId) {
          const orderExists = unpickedOrders.find(order => order.order_id === picker.orderId);
          if (!orderExists) {
            picker.active = false;
            picker.orderId = null;
            picker.progress = 0;
          }
        }
      });
  
      // Assign new orders to inactive pickers
      this.pickers.forEach(picker => {
        if (!picker.active && orderIndex < unpickedOrders.length) {
          const order = unpickedOrders[orderIndex];
          picker.active = true;
          picker.orderId = order.order_id;
          picker.progress = picker.progress || Math.floor(Math.random() * 30); // Random starting progress
          orderIndex++;
        }
      });
  
      // Update active and queued orders
      this.activeOrders = unpickedOrders.slice(0, 5);
      this.queuedOrders = unpickedOrders.slice(5);
    }
  
    renderPickingDashboard() {
      this.renderActivePicks();
      this.renderQueue();
    }
  
    renderActivePicks() {
      const container = document.getElementById('active-picks-grid');
      if (!container) return;
  
      container.innerHTML = '';
  
      this.pickers.forEach(picker => {
        const card = document.createElement('div');
        card.className = 'picking-card';
        
        if (picker.active && picker.orderId) {
          const order = this.allOrders[Object.keys(this.allOrders).find(key => 
            this.allOrders[key].order_id === picker.orderId
          )];
          
          if (order) {
            card.innerHTML = `
              <div class="picker-header">
                <div class="picker-info">
                  <span class="picker-name">👤 ${picker.name}</span>
                  <span class="picker-status active">🟢 Active</span>
                </div>
              </div>
              <div class="order-info">
                <h4>📦 ${order.order_id}</h4>
                <div class="order-items">
                  <strong>Items:</strong> ${order.order_items.join(', ')}
                </div>
                <div class="order-location">
                  <strong>Location:</strong> ${order.delivery_location.lat.toFixed(3)}, ${order.delivery_location.lng.toFixed(3)}
                </div>
              </div>
              <div class="progress-section">
                <div class="progress-bar">
                  <div class="progress-fill" style="width: ${picker.progress}%"></div>
                </div>
                <span class="progress-text">${picker.progress}% Complete</span>
              </div>
              <div class="picking-actions">
                <button class="btn btn-sm btn-success" onclick="pickingManager.completeOrder('${picker.orderId}', ${picker.id})">
                  ✅ Mark Complete
                </button>
              </div>
            `;
          }
        } else {
          card.innerHTML = `
            <div class="picker-header">
              <div class="picker-info">
                <span class="picker-name">👤 ${picker.name}</span>
                <span class="picker-status idle">⚪ Idle</span>
              </div>
            </div>
            <div class="idle-state">
              <div class="idle-icon">💤</div>
              <p>Waiting for orders...</p>
            </div>
          `;
          card.classList.add('idle');
        }
  
        container.appendChild(card);
      });
    }
  
    renderQueue() {
      const container = document.getElementById('queue-list');
      if (!container) return;
  
      container.innerHTML = '';
  
      if (this.queuedOrders.length === 0) {
        container.innerHTML = '<div class="empty-queue">📭 No orders in queue</div>';
        return;
      }
  
      this.queuedOrders.forEach((order, index) => {
        const queueItem = document.createElement('div');
        queueItem.className = 'queue-item';
        queueItem.innerHTML = `
          <div class="queue-position">#${index + 1}</div>
          <div class="queue-order-info">
            <strong>📦 ${order.order_id}</strong>
            <div class="queue-items">${order.order_items.join(', ')}</div>
          </div>
          <div class="queue-eta">ETA: ${(index + 1) * 3}min</div>
        `;
        container.appendChild(queueItem);
      });
    }
  
    completeOrder(orderId, pickerId) {
      // Update order status in Firebase
      const orderKey = Object.keys(this.allOrders).find(key => 
        this.allOrders[key].order_id === orderId
      );
      
      if (orderKey) {
        firebase.database().ref(`orders/${orderKey}/current_status`).set('Picked');
      }
  
      // Reset picker
      const picker = this.pickers.find(p => p.id === pickerId);
      if (picker) {
        picker.active = false;
        picker.orderId = null;
        picker.progress = 0;
      }
  
      // Force update
      setTimeout(() => {
        this.updateOrders(this.allOrders);
      }, 500);
    }
  
    startProgressSimulation() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval);
      }
  
      this.progressInterval = setInterval(() => {
        let updated = false;
        
        this.pickers.forEach(picker => {
          if (picker.active && picker.progress < 100) {
            // Simulate progress increase
            picker.progress += Math.floor(Math.random() * 3) + 1;
            if (picker.progress > 100) picker.progress = 100;
            updated = true;
          }
        });
  
        if (updated) {
          this.renderActivePicks();
        }
      }, 3000); // Update every 3 seconds
    }
  
    stopProgressSimulation() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
      }
    }
  }
  
  // Global instance
  const pickingManager = new PickingManager();
  
  // Global functions for integration
  window.initializePickingDashboard = function() {
    pickingManager.initializeDashboard();
  };
  
  window.updatePickingDashboard = function(orders) {
    pickingManager.updateOrders(orders);
  };
  
  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    pickingManager.stopProgressSimulation();
  });