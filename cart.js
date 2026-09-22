// Cart Manager using localStorage
const cartManager = {
    key: 'novastore_cart_items',

    getItems() {
        try {
            return JSON.parse(localStorage.getItem(this.key)) || [];
        } catch (e) {
            return [];
        }
    },

    saveItems(items) {
        localStorage.setItem(this.key, JSON.stringify(items));
        this.updateUI();
    },

    addItem(product) {
        let items = this.getItems();
        const existingIndex = items.findIndex(item => item.id === product.id);

        if (existingIndex > -1) {
            const currentQty = items[existingIndex].quantity;
            if (product.stock && currentQty >= product.stock) {
                this.showToast(`Only ${product.stock} units available in stock.`, 'warning');
                return false;
            }
            items[existingIndex].quantity += 1;
        } else {
            if (product.stock && product.stock <= 0) {
                this.showToast('Sorry, this product is currently out of stock.', 'danger');
                return false;
            }
            items.push({
                id: product.id,
                name: product.name,
                price: parseFloat(product.price),
                image_url: product.image_url,
                stock: product.stock,
                quantity: 1
            });
        }

        this.saveItems(items);
        this.showToast(`Added "${product.name}" to cart!`, 'success');

        // Optional: auto-open drawer
        const drawerEl = document.getElementById('cartOffcanvas');
        if (drawerEl && bootstrap.Offcanvas.getInstance(drawerEl)) {
            // Already open
        } else if (drawerEl) {
            const bsOffcanvas = new bootstrap.Offcanvas(drawerEl);
            bsOffcanvas.show();
        }
        return true;
    },

    updateQuantity(productId, delta) {
        let items = this.getItems();
        const item = items.find(i => i.id === productId);
        if (!item) return;

        const newQty = item.quantity + delta;
        if (newQty <= 0) {
            this.removeItem(productId);
            return;
        }

        if (item.stock && newQty > item.stock) {
            this.showToast(`Cannot exceed available stock (${item.stock})`, 'warning');
            return;
        }

        item.quantity = newQty;
        this.saveItems(items);
    },

    removeItem(productId) {
        let items = this.getItems();
        items = items.filter(item => item.id !== productId);
        this.saveItems(items);
        this.showToast('Item removed from cart', 'info');
    },

    clearCart() {
        localStorage.removeItem(this.key);
        this.updateUI();
    },

    calculateTotals() {
        const items = this.getItems();
        const totalCount = items.reduce((sum, item) => sum + item.quantity, 0);
        const subtotal = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        return { totalCount, subtotal };
    },

    updateUI() {
        const items = this.getItems();
        const { totalCount, subtotal } = this.calculateTotals();

        // Update badges
        const badge = document.getElementById('cartBadge');
        if (badge) badge.innerText = totalCount;

        const drawerCount = document.getElementById('cartDrawerCount');
        if (drawerCount) drawerCount.innerText = `${totalCount} item${totalCount === 1 ? '' : 's'}`;

        const subtotalEl = document.getElementById('cartSubtotal');
        if (subtotalEl) subtotalEl.innerText = `$${subtotal.toFixed(2)}`;

        // Checkout button state
        const checkoutBtn = document.getElementById('proceedToCheckoutBtn');
        if (checkoutBtn) {
            if (items.length === 0) {
                checkoutBtn.classList.add('disabled');
            } else {
                checkoutBtn.classList.remove('disabled');
            }
        }

        // Render Drawer List
        const listContainer = document.getElementById('cartItemsList');
        if (listContainer) {
            if (items.length === 0) {
                listContainer.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="fa-solid fa-cart-arrow-down fa-3x mb-3 text-secondary opacity-50"></i>
                        <h6>Your cart is empty</h6>
                        <p class="small">Add some great items from the catalog!</p>
                    </div>
                `;
            } else {
                let html = '';
                items.forEach(item => {
                    const itemTotal = (item.price * item.quantity).toFixed(2);
                    html += `
                        <div class="cart-item">
                            <img src="${item.image_url || 'https://via.placeholder.com/60'}" class="cart-item-img" alt="${item.name}">
                            <div class="flex-grow-1 min-w-0">
                                <h6 class="mb-1 text-truncate fs-6" title="${item.name}">${item.name}</h6>
                                <div class="text-primary fw-bold small">$${item.price.toFixed(2)}</div>
                                <div class="d-flex align-items-center gap-2 mt-2">
                                    <button class="qty-btn" onclick="cartManager.updateQuantity(${item.id}, -1)">
                                        <i class="fa-solid fa-minus small"></i>
                                    </button>
                                    <span class="fw-semibold px-1 small">${item.quantity}</span>
                                    <button class="qty-btn" onclick="cartManager.updateQuantity(${item.id}, 1)">
                                        <i class="fa-solid fa-plus small"></i>
                                    </button>
                                    <span class="text-muted small ms-auto fw-semibold">$${itemTotal}</span>
                                </div>
                            </div>
                            <button class="btn btn-sm text-danger p-0 ms-2" title="Remove item" onclick="cartManager.removeItem(${item.id})">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    `;
                });
                listContainer.innerHTML = html;
            }
        }

        // Render Checkout page summary if present
        this.renderCheckoutSummary();
    },

    renderCheckoutSummary() {
        const checkoutList = document.getElementById('checkoutSummaryItems');
        const checkoutSubtotal = document.getElementById('checkoutSubtotal');
        const checkoutShipping = document.getElementById('checkoutShipping');
        const checkoutTotal = document.getElementById('checkoutTotal');

        if (!checkoutList) return;

        const items = this.getItems();
        const { subtotal } = this.calculateTotals();
        const shippingFee = subtotal >= 50 || subtotal === 0 ? 0.00 : 9.99;
        const finalTotal = subtotal + shippingFee;

        if (items.length === 0) {
            checkoutList.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <p>No items in cart.</p>
                    <a href="/" class="btn btn-sm btn-outline-primary rounded-pill">Continue Shopping</a>
                </div>
            `;
            const submitBtn = document.getElementById('placeOrderBtn');
            if (submitBtn) submitBtn.disabled = true;
        } else {
            let html = '';
            items.forEach(item => {
                html += `
                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                        <div class="d-flex align-items-center gap-2">
                            <img src="${item.image_url}" class="rounded" width="48" height="48" style="object-fit:cover;">
                            <div>
                                <h6 class="mb-0 small fw-bold">${item.name}</h6>
                                <span class="text-muted small">Qty: ${item.quantity} × $${item.price.toFixed(2)}</span>
                            </div>
                        </div>
                        <span class="fw-semibold small">$${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                `;
            });
            checkoutList.innerHTML = html;

            const submitBtn = document.getElementById('placeOrderBtn');
            if (submitBtn) submitBtn.disabled = false;
        }

        if (checkoutSubtotal) checkoutSubtotal.innerText = `$${subtotal.toFixed(2)}`;
        if (checkoutShipping) checkoutShipping.innerText = shippingFee === 0 ? 'FREE' : `$${shippingFee.toFixed(2)}`;
        if (checkoutTotal) checkoutTotal.innerText = `$${finalTotal.toFixed(2)}`;
    },

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastFloatingContainer');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toastFloatingContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1090';
            document.body.appendChild(container);
        }

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : type === 'warning' ? 'warning text-dark' : type === 'success' ? 'success' : 'primary'} border-0 shadow`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body fw-medium">
                    ${message}
                </div>
                <button type="button" class="btn-close ${type === 'warning' ? '' : 'btn-close-white'} me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.getElementById('toastFloatingContainer').appendChild(toastEl);
        const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
        bsToast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }
};

// Initialize Cart on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    cartManager.updateUI();

    // Hook Checkout Form Submission
    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('placeOrderBtn');
            const items = cartManager.getItems();

            if (items.length === 0) {
                cartManager.showToast('Your cart is empty. Please add products first.', 'danger');
                return;
            }

            const payload = {
                customer_name: document.getElementById('customer_name').value,
                customer_email: document.getElementById('customer_email').value,
                customer_phone: document.getElementById('customer_phone').value,
                shipping_address: document.getElementById('shipping_address').value,
                payment_method: document.querySelector('input[name="payment_method"]:checked')?.value || 'Credit Card',
                items: items.map(i => ({ id: i.id, quantity: i.quantity }))
            };

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Placing Order...';

            try {
                const response = await fetch('/api/checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const resData = await response.json();

                if (!response.ok || resData.error) {
                    cartManager.showToast(resData.error || 'Failed to place order.', 'danger');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fa-solid fa-lock me-2"></i> Complete Order';
                    return;
                }

                // Success! Clear cart and redirect
                cartManager.clearCart();
                window.location.href = resData.redirect_url;
            } catch (err) {
                console.error(err);
                cartManager.showToast('Network error while placing order.', 'danger');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa-solid fa-lock me-2"></i> Complete Order';
            }
        });
    }
});
