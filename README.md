# NovaStore - Modern E-Commerce Platform

A feature-complete, modern online store built with **Python (Flask)**, **SQLite**, and responsive **Bootstrap 5**, featuring full product catalog management, interactive shopping cart, simulated checkout, and real-time visual order tracking.

---

## Key Features

### 🛒 Customer Storefront
- **Browse & Filter**: Filter by categories (Electronics, Fashion, Home & Living, Books), search by title/description keywords, and sort by price or newest arrivals.
- **Stock Indicators**: Real-time stock status badges (`In Stock`, `Low Stock (≤ 5 units)`, `Out of Stock`).
- **Quick View Modal**: Inspect high-resolution images, detailed descriptions, and instant add-to-cart without navigating away.
- **Persistent Cart Drawer**: Offcanvas shopping cart powered by `localStorage` that preserves cart items across page refreshes.
- **Fast Checkout Flow**: Enter shipping and contact details, choose simulated payment method (Credit/Debit Card, UPI / Instant Pay, or Cash on Delivery), with automated inventory validation and deduction.

### 📦 Order Tracking Hub (`/track`)
- **Direct Order Lookup**: Track any order by its unique Order ID (e.g. `ORD-782410`) or by customer email address.
- **Visual Progress Stepper**: 5-stage graphical timeline (`Placed` ➔ `Processing` ➔ `Shipped` ➔ `Out for Delivery` ➔ `Delivered`).
- **Activity Checkpoints & Notes**: Timestamped chronological log displaying carrier updates, dispatch notes, and fulfillment milestones.
- **Order Receipts**: Printable itemized receipts displaying prices, quantities, and delivery destinations.

### ⚙️ Product Management (`/admin/products`)
- **Catalog Metrics**: Instant overview of Total Items, Low Stock alerts, and Out-of-Stock count.
- **Full CRUD Operations**:
  - **Add Product**: Set title, category, price, stock quantity, image URL, and description.
  - **Edit Product**: Update prices, adjust inventory stock levels, or change imagery.
  - **Delete Product**: Remove discontinued items with safety confirmation.

### 📋 Order Operations (`/admin/orders`)
- **Fulfillment Dashboard**: Filter orders by status (`Placed`, `Processing`, `Shipped`, `Out for Delivery`, `Delivered`, `Cancelled`).
- **Status Progression**: Update order statuses and append custom notes (e.g., courier tracking numbers, transit updates) that sync instantly to the customer's tracking view.

---

## Quick Start

### 1. Launch the Server
Ensure Python 3.x is available and run:

```powershell
python app.py
```

The application will start on:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

*(The database `instance/store.db` is initialized and pre-seeded automatically on first startup).*

### 2. Pre-Seeded Demo Test Orders
To immediately test order tracking without creating an order:
- **Order ID**: `ORD-782410` (Status: *Shipped* - Customer: Alex Morgan)
- **Order ID**: `ORD-492105` (Status: *Delivered* - Customer: Sarah Connor)

Or place a brand new order from the catalog to receive a newly generated tracking code!

---

## Running Automated Tests

Run the automated test suite covering catalog queries, stock controls, admin CRUD, and order lifecycle transitions:

```powershell
python test_app.py
```

---

## Project Structure

```text
├── app.py                  # Main Flask web application & REST routes
├── models.py               # SQLAlchemy database schemas (Product, Order, OrderItem, History)
├── seed_data.py            # Initial catalog & demo orders seeder
├── test_app.py             # Automated unit tests
├── templates/
│   ├── base.html           # Master layout, navigation, cart drawer, footer
│   ├── index.html          # Storefront catalog, filter pills, product grid, quick view
│   ├── checkout.html       # Checkout form with dynamic cart summary
│   ├── track_lookup.html   # Order search portal & demo order shortcuts
│   ├── track_order.html    # Visual stepper tracking timeline & receipt
│   ├── admin_products.html # Product management dashboard (CRUD)
│   └── admin_orders.html   # Order operations & status management
└── static/
    ├── css/styles.css      # Custom styling, animations, stepper styles
    └── js/cart.js          # Client-side cart manager & checkout handler
```
