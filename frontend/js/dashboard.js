const db = firebase.database();
const ordersRef = db.ref("orders");

const activeOrdersEl = document.getElementById("active-orders");
const completedOrdersEl = document.getElementById("completed-orders");

const totalEl = document.getElementById("total-orders");
const unpickedEl = document.getElementById("unpicked-count");
const pickedEl = document.getElementById("picked-count");
const deliveredEl = document.getElementById("delivered-count");
const delayedEl = document.getElementById("delayed-count");

ordersRef.on("value", snapshot => {
  const orders = snapshot.val();
  activeOrdersEl.innerHTML = "";
  completedOrdersEl.innerHTML = "";

  let total = 0, unpicked = 0, picked = 0, delivered = 0, delayed = 0;

  for (let key in orders) {
    const order = orders[key];
    total++;
    const status = order.current_status || "Unpicked";
    const sla = order.SLA_status || "";

    if (status === "Delivered") {
      delivered++;
      if (sla === "❌ Delayed") delayed++;
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${order.order_id}</td><td>${order.order_items.join(", ")}</td><td>${new Date().toLocaleTimeString()}</td><td>${sla || "✅ On time"}</td>`;
      completedOrdersEl.appendChild(tr);
    } else {
      if (status === "Unpicked") unpicked++;
      if (status === "Picked") picked++;
      if (sla === "❌ Delayed") delayed++;
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${order.order_id}</td><td>${order.order_items.join(", ")}</td><td>${order.delivery_location.lat.toFixed(3)}, ${order.delivery_location.lng.toFixed(3)}</td><td>${status}</td><td>${sla || "⏳ Pending"}</td>`;
      activeOrdersEl.appendChild(tr);
    }
  }

  totalEl.textContent = total;
  unpickedEl.textContent = unpicked;
  pickedEl.textContent = picked;
  deliveredEl.textContent = delivered;
  delayedEl.textContent = delayed;

  // Update picking dashboard if it's active
  if (window.updatePickingDashboard) {
    window.updatePickingDashboard(orders);
  }
});

function switchTab(tab) {
  // Hide all tabs
  document.getElementById("dashboard-tab").style.display = "none";
  document.getElementById("orders-tab").style.display = "none";
  document.getElementById("picking-tab").style.display = "none";
  
  // Remove active class from all nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
  });
  
  // Show selected tab
  document.getElementById(tab + "-tab").style.display = "block";
  
  // Add active class to clicked nav link
  event.target.classList.add('active');
  
  // Initialize picking dashboard when switching to it
  if (tab === 'picking' && window.initializePickingDashboard) {
    window.initializePickingDashboard();
  }
}