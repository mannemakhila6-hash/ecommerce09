from datetime import datetime, timedelta, timezone
from models import db, Product, Order, OrderItem, OrderStatusHistory

SAMPLE_PRODUCTS = [
    {
        "name": "Wireless Noise-Canceling Headphones",
        "description": "High-fidelity audio with active noise cancellation, 30-hour battery life, and ultra-plush memory foam earcups.",
        "price": 99.99,
        "category": "Electronics",
        "stock_quantity": 24,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "Ergonomic Mechanical Keyboard",
        "description": "Compact 75% layout with hot-swappable mechanical switches, RGB backlighting, and bluetooth multi-device connectivity.",
        "price": 79.50,
        "category": "Electronics",
        "stock_quantity": 18,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "Minimalist Classic Watch",
        "description": "Sleek stainless steel case with genuine leather strap, water-resistant up to 50 meters, and sapphire crystal glass.",
        "price": 129.00,
        "category": "Fashion",
        "stock_quantity": 12,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "Vintage Washed Denim Jacket",
        "description": "Timeless relaxed fit crafted from 100% heavyweight cotton denim with antique brass buttons and deep interior pockets.",
        "price": 64.99,
        "category": "Fashion",
        "stock_quantity": 15,
        "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "Ceramic Pour-Over Coffee Dripper",
        "description": "Artisan matte ceramic dripper engineered for optimal extraction rate and rich, clean artisanal coffee flavors.",
        "price": 32.50,
        "category": "Home & Living",
        "stock_quantity": 20,
        "image_url": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "Insulated Thermal Water Bottle",
        "description": "Vacuum-insulated double-wall stainless steel bottle that keeps drinks ice-cold for 24 hours or piping hot for 12 hours.",
        "price": 24.99,
        "category": "Home & Living",
        "stock_quantity": 35,
        "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Art of Modern Software Design",
        "description": "Comprehensive hardcover guide covering clean architecture, design patterns, microservices, and reliable engineering principles.",
        "price": 39.99,
        "category": "Books",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3777a?w=600&auto=format&fit=crop&q=80"
    },
    {
        "name": "Smart Fitness & Activity Tracker",
        "description": "Heart rate tracking, SpO2 sensor, sleep analytics, 5ATM water resistance, and crisp AMOLED display. (Low stock!)",
        "price": 49.99,
        "category": "Electronics",
        "stock_quantity": 3,
        "image_url": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=600&auto=format&fit=crop&q=80"
    }
]

def seed_database(app):
    with app.app_context():
        # Check if already seeded
        if db.session.query(Product.id).first() is not None:
            return

        print("Seeding initial products...")
        products = []
        for item in SAMPLE_PRODUCTS:
            prod = Product(**item)
            db.session.add(prod)
            products.append(prod)
        db.session.commit()

        # Seed sample orders for immediate tracking demonstration
        print("Seeding sample orders for tracking...")
        now = datetime.now(timezone.utc)

        # Order 1: In transit (Shipped)
        order1 = Order(
            id="ORD-782410",
            customer_name="Alex Morgan",
            customer_email="alex.morgan@example.com",
            customer_phone="+1 (555) 234-5678",
            shipping_address="742 Evergreen Terrace, Springfield, OR 97477",
            payment_method="Credit Card",
            total_amount=179.49,
            status="Shipped",
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(hours=6)
        )
        db.session.add(order1)
        db.session.flush()

        item1_1 = OrderItem(
            order_id=order1.id,
            product_id=products[0].id,
            product_name=products[0].name,
            price_at_purchase=99.99,
            quantity=1,
            subtotal=99.99
        )
        item1_2 = OrderItem(
            order_id=order1.id,
            product_id=products[1].id,
            product_name=products[1].name,
            price_at_purchase=79.50,
            quantity=1,
            subtotal=79.50
        )
        db.session.add_all([item1_1, item1_2])

        hist1_1 = OrderStatusHistory(
            order_id=order1.id,
            status="Placed",
            notes="Order placed and payment authorized.",
            timestamp=now - timedelta(days=2)
        )
        hist1_2 = OrderStatusHistory(
            order_id=order1.id,
            status="Processing",
            notes="Order packed at central fulfillment hub.",
            timestamp=now - timedelta(days=1, hours=12)
        )
        hist1_3 = OrderStatusHistory(
            order_id=order1.id,
            status="Shipped",
            notes="Handed over to Express Courier (Tracking: EXP-9920148). In transit to destination.",
            timestamp=now - timedelta(hours=6)
        )
        db.session.add_all([hist1_1, hist1_2, hist1_3])

        # Order 2: Delivered
        order2 = Order(
            id="ORD-492105",
            customer_name="Sarah Connor",
            customer_email="sarah.c@example.com",
            customer_phone="+1 (555) 876-5432",
            shipping_address="1204 Cyber Way, Los Angeles, CA 90001",
            payment_method="UPI / Instant Bank Transfer",
            total_amount=129.00,
            status="Delivered",
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=1)
        )
        db.session.add(order2)
        db.session.flush()

        item2_1 = OrderItem(
            order_id=order2.id,
            product_id=products[2].id,
            product_name=products[2].name,
            price_at_purchase=129.00,
            quantity=1,
            subtotal=129.00
        )
        db.session.add(item2_1)

        hist2_1 = OrderStatusHistory(order_id=order2.id, status="Placed", notes="Order placed successfully.", timestamp=now - timedelta(days=4))
        hist2_2 = OrderStatusHistory(order_id=order2.id, status="Processing", notes="Verified & packaged.", timestamp=now - timedelta(days=3))
        hist2_3 = OrderStatusHistory(order_id=order2.id, status="Shipped", notes="Departed transit facility.", timestamp=now - timedelta(days=2))
        hist2_4 = OrderStatusHistory(order_id=order2.id, status="Out for Delivery", notes="Out with courier driver for delivery.", timestamp=now - timedelta(days=1, hours=4))
        hist2_5 = OrderStatusHistory(order_id=order2.id, status="Delivered", notes="Package handed to resident. Signed by S. Connor.", timestamp=now - timedelta(days=1))
        db.session.add_all([hist2_1, hist2_2, hist2_3, hist2_4, hist2_5])

        db.session.commit()
        print("Database successfully initialized and seeded!")
