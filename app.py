import os
import uuid
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Product, Order, OrderItem, OrderStatusHistory
from seed_data import seed_database

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ecommerce-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

ORDER_STATUS_FLOW = ['Placed', 'Processing', 'Shipped', 'Out for Delivery', 'Delivered']

# Initialize database & seed data if empty
with app.app_context():
    db.create_all()
    seed_database(app)

# Context processor for cart badge and global counts
@app.context_processor
def inject_globals():
    categories = [c[0] for c in db.session.query(Product.category).distinct().all()]
    return {
        'all_categories': sorted(categories),
        'status_flow': ORDER_STATUS_FLOW
    }

# -------------------------------------------------------------
# Customer Storefront Routes
# -------------------------------------------------------------

@app.route('/')
def storefront():
    category = request.args.get('category', '').strip()
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'newest')

    query = Product.query

    if category and category != 'All':
        query = query.filter(Product.category == category)

    if search_query:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%')
            )
        )

    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.all()
    return render_template('index.html', products=products, active_category=category, search_query=search_query, sort_by=sort_by)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)
    return jsonify(product.to_dict())

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

@app.route('/api/checkout', methods=['POST'])
def process_checkout():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    customer_name = data.get('customer_name', '').strip()
    customer_email = data.get('customer_email', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    shipping_address = data.get('shipping_address', '').strip()
    payment_method = data.get('payment_method', 'Credit / Debit Card')
    cart_items = data.get('items', [])

    if not customer_name or not customer_email or not shipping_address:
        return jsonify({'error': 'Please provide full name, email, and shipping address.'}), 400

    if not cart_items or not isinstance(cart_items, list):
        return jsonify({'error': 'Your cart is empty.'}), 400

    # Stock validation and order preparation
    total_amount = 0.0
    items_to_create = []

    for item in cart_items:
        prod_id = item.get('id')
        qty = int(item.get('quantity', 1))

        if qty <= 0:
            continue

        product = db.session.get(Product, prod_id)
        if not product:
            return jsonify({'error': f"Product ID {prod_id} no longer exists."}), 400

        if product.stock_quantity < qty:
            return jsonify({
                'error': f"Insufficient stock for '{product.name}'. Only {product.stock_quantity} left in stock."
            }), 400

        subtotal = round(product.price * qty, 2)
        total_amount += subtotal

        # Deduct stock
        product.stock_quantity -= qty

        items_to_create.append({
            'product_id': product.id,
            'product_name': product.name,
            'price': product.price,
            'quantity': qty,
            'subtotal': subtotal
        })

    # Generate unique readable order ID (e.g., ORD-A93B2F)
    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"

    new_order = Order(
        id=order_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        shipping_address=shipping_address,
        payment_method=payment_method,
        total_amount=round(total_amount, 2),
        status='Placed'
    )
    db.session.add(new_order)
    db.session.flush()

    for item_data in items_to_create:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data['product_id'],
            product_name=item_data['product_name'],
            price_at_purchase=item_data['price'],
            quantity=item_data['quantity'],
            subtotal=item_data['subtotal']
        )
        db.session.add(order_item)

    initial_history = OrderStatusHistory(
        order_id=new_order.id,
        status='Placed',
        notes=f"Order successfully placed via {payment_method}. Confirmation sent to {customer_email}."
    )
    db.session.add(initial_history)

    db.session.commit()

    return jsonify({
        'success': True,
        'order_id': new_order.id,
        'redirect_url': url_for('track_order_view', order_id=new_order.id)
    })

# -------------------------------------------------------------
# Order Tracking Routes
# -------------------------------------------------------------

@app.route('/track', methods=['GET', 'POST'])
def track_lookup():
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if not query:
            flash('Please enter an Order ID or email address to search.', 'warning')
            return redirect(url_for('track_lookup'))

        # Check if direct order ID
        order = db.session.get(Order, query.upper())
        if order:
            return redirect(url_for('track_order_view', order_id=order.id))

        # Check by email
        orders_by_email = Order.query.filter(Order.customer_email.ilike(query)).order_by(Order.created_at.desc()).all()
        if orders_by_email:
            return render_template('track_lookup.html', orders=orders_by_email, search_query=query)

        flash(f"No orders found matching '{query}'. Please verify your Order ID or email address.", 'danger')
        return redirect(url_for('track_lookup'))

    # GET request - show tracker search page and recent orders for demo convenience
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('track_lookup.html', recent_orders=recent_orders)

@app.route('/track/<order_id>')
def track_order_view(order_id):
    order = db.get_or_404(Order, order_id.upper())

    # Calculate status progress index
    status_order = ['Placed', 'Processing', 'Shipped', 'Out for Delivery', 'Delivered']
    current_index = -1
    if order.status in status_order:
        current_index = status_order.index(order.status)
    is_cancelled = (order.status == 'Cancelled')

    return render_template(
        'track_order.html',
        order=order,
        status_flow=status_order,
        current_index=current_index,
        is_cancelled=is_cancelled
    )

@app.route('/api/orders/<order_id>')
def api_order_status(order_id):
    order = db.get_or_404(Order, order_id.upper())
    return jsonify(order.to_dict())

# -------------------------------------------------------------
# Admin - Product Management Routes
# -------------------------------------------------------------

@app.route('/admin')
def admin_root():
    return redirect(url_for('admin_products'))

@app.route('/admin/products')
def admin_products():
    category = request.args.get('category', '').strip()
    search = request.args.get('q', '').strip()

    query = Product.query
    if category and category != 'All':
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.id.desc()).all()

    # Metrics
    total_products = Product.query.count()
    low_stock_count = Product.query.filter(Product.stock_quantity > 0, Product.stock_quantity <= 5).count()
    out_of_stock_count = Product.query.filter(Product.stock_quantity == 0).count()

    return render_template(
        'admin_products.html',
        products=products,
        active_category=category,
        search_query=search,
        total_products=total_products,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )

@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    name = request.form.get('name', '').strip()
    price_val = request.form.get('price', '').strip()
    stock_val = request.form.get('stock_quantity', '').strip()
    category = request.form.get('category', 'General').strip()
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if not name or not price_val:
        flash('Product name and price are required.', 'danger')
        return redirect(url_for('admin_products'))

    try:
        price = float(price_val)
        stock_quantity = int(stock_val) if stock_val else 0
    except ValueError:
        flash('Invalid price or stock quantity value.', 'danger')
        return redirect(url_for('admin_products'))

    if not image_url:
        image_url = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&auto=format&fit=crop&q=80"

    new_prod = Product(
        name=name,
        description=description,
        price=price,
        category=category,
        stock_quantity=stock_quantity,
        image_url=image_url
    )
    db.session.add(new_prod)
    db.session.commit()
    flash(f"Product '{new_prod.name}' added successfully!", 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/<int:product_id>/edit', methods=['POST'])
def admin_edit_product(product_id):
    product = db.get_or_404(Product, product_id)

    name = request.form.get('name', '').strip()
    price_val = request.form.get('price', '').strip()
    stock_val = request.form.get('stock_quantity', '').strip()
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if not name or not price_val:
        flash('Product name and price are required.', 'danger')
        return redirect(url_for('admin_products'))

    try:
        product.price = float(price_val)
        product.stock_quantity = int(stock_val) if stock_val else 0
    except ValueError:
        flash('Invalid price or stock quantity value.', 'danger')
        return redirect(url_for('admin_products'))

    product.name = name
    product.category = category if category else 'General'
    product.description = description
    if image_url:
        product.image_url = image_url

    db.session.commit()
    flash(f"Product '{product.name}' updated successfully!", 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
def admin_delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{name}' has been deleted.", 'info')
    return redirect(url_for('admin_products'))

# -------------------------------------------------------------
# Admin - Order Management Routes
# -------------------------------------------------------------

@app.route('/admin/orders')
def admin_orders():
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('q', '').strip()

    query = Order.query
    if status_filter and status_filter != 'All':
        query = query.filter(Order.status == status_filter)

    if search:
        query = query.filter(
            db.or_(
                Order.id.ilike(f'%{search}%'),
                Order.customer_name.ilike(f'%{search}%'),
                Order.customer_email.ilike(f'%{search}%')
            )
        )

    orders = query.order_by(Order.created_at.desc()).all()

    # Status counts for dashboard metrics
    counts = {
        'all': Order.query.count(),
        'Placed': Order.query.filter_by(status='Placed').count(),
        'Processing': Order.query.filter_by(status='Processing').count(),
        'Shipped': Order.query.filter_by(status='Shipped').count(),
        'Out for Delivery': Order.query.filter_by(status='Out for Delivery').count(),
        'Delivered': Order.query.filter_by(status='Delivered').count(),
        'Cancelled': Order.query.filter_by(status='Cancelled').count(),
    }

    return render_template(
        'admin_orders.html',
        orders=orders,
        status_filter=status_filter,
        search_query=search,
        counts=counts,
        status_flow=ORDER_STATUS_FLOW + ['Cancelled']
    )

@app.route('/admin/orders/<order_id>/status', methods=['POST'])
def admin_update_order_status(order_id):
    order = db.get_or_404(Order, order_id.upper())
    new_status = request.form.get('status', '').strip()
    notes = request.form.get('notes', '').strip()

    if not new_status:
        flash('Status is required.', 'danger')
        return redirect(url_for('admin_orders'))

    old_status = order.status
    order.status = new_status
    now = datetime.now(timezone.utc)
    order.updated_at = now

    note_text = notes if notes else f"Status updated from '{old_status}' to '{new_status}' by Admin."
    history_entry = OrderStatusHistory(
        order_id=order.id,
        status=new_status,
        notes=note_text,
        timestamp=now
    )
    db.session.add(history_entry)
    db.session.commit()

    flash(f"Order #{order.id} status updated to '{new_status}'!", 'success')
    return redirect(request.referrer or url_for('admin_orders'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
