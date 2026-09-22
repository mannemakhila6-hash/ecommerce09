import unittest
from app import app, db
from models import Product, Order, OrderItem, OrderStatusHistory

class TestOnlineStore(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            # Seed test product
            self.p1 = Product(
                name="Test Headphones",
                description="High quality test sound",
                price=50.0,
                category="Electronics",
                stock_quantity=10,
                image_url="https://via.placeholder.com/150"
            )
            self.p2 = Product(
                name="Test Book",
                description="Clean architecture guide",
                price=20.0,
                category="Books",
                stock_quantity=2,
                image_url="https://via.placeholder.com/150"
            )
            db.session.add_all([self.p1, self.p2])
            db.session.commit()
            self.p1_id = self.p1.id
            self.p2_id = self.p2.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_storefront_catalog(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Headphones', response.data)
        self.assertIn(b'Test Book', response.data)

    def test_filter_and_search(self):
        # Filter by Category
        resp_filter = self.client.get('/?category=Electronics')
        self.assertEqual(resp_filter.status_code, 200)
        self.assertIn(b'Test Headphones', resp_filter.data)
        self.assertNotIn(b'Test Book', resp_filter.data)

        # Search by Query
        resp_search = self.client.get('/?q=architecture')
        self.assertEqual(resp_search.status_code, 200)
        self.assertIn(b'Test Book', resp_search.data)
        self.assertNotIn(b'Test Headphones', resp_search.data)

    def test_admin_add_and_edit_product(self):
        # Add Product
        resp_add = self.client.post('/admin/products/add', data={
            'name': 'Ergonomic Mouse',
            'price': '35.00',
            'stock_quantity': '15',
            'category': 'Electronics',
            'description': 'Comfortable wireless mouse',
            'image_url': 'https://via.placeholder.com/150'
        }, follow_redirects=True)
        self.assertEqual(resp_add.status_code, 200)

        with app.app_context():
            new_prod = Product.query.filter_by(name='Ergonomic Mouse').first()
            self.assertIsNotNone(new_prod)
            self.assertEqual(new_prod.price, 35.0)
            self.assertEqual(new_prod.stock_quantity, 15)

            # Edit Product
            resp_edit = self.client.post(f'/admin/products/{new_prod.id}/edit', data={
                'name': 'Ergonomic Mouse V2',
                'price': '39.99',
                'stock_quantity': '12',
                'category': 'Electronics',
                'description': 'Upgraded sensor',
                'image_url': 'https://via.placeholder.com/150'
            }, follow_redirects=True)
            self.assertEqual(resp_edit.status_code, 200)

            updated = db.session.get(Product, new_prod.id)
            self.assertEqual(updated.name, 'Ergonomic Mouse V2')
            self.assertEqual(updated.price, 39.99)
            self.assertEqual(updated.stock_quantity, 12)

    def test_checkout_and_stock_deduction(self):
        checkout_payload = {
            'customer_name': 'Alice Smith',
            'customer_email': 'alice@example.com',
            'customer_phone': '555-1234',
            'shipping_address': '100 Main St, Metropolis',
            'payment_method': 'Credit / Debit Card',
            'items': [
                {'id': self.p1_id, 'quantity': 2},
                {'id': self.p2_id, 'quantity': 1}
            ]
        }

        resp = self.client.post('/api/checkout', json=checkout_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        order_id = data['order_id']
        self.assertTrue(order_id.startswith('ORD-'))

        with app.app_context():
            # Check stock deduction
            p1 = db.session.get(Product, self.p1_id)
            p2 = db.session.get(Product, self.p2_id)
            self.assertEqual(p1.stock_quantity, 8)  # 10 - 2
            self.assertEqual(p2.stock_quantity, 1)  # 2 - 1

            # Check order record
            order = db.session.get(Order, order_id)
            self.assertIsNotNone(order)
            self.assertEqual(order.customer_name, 'Alice Smith')
            self.assertEqual(order.total_amount, 120.0)  # (50 * 2) + (20 * 1)
            self.assertEqual(order.status, 'Placed')
            self.assertEqual(len(order.items), 2)
            self.assertEqual(len(order.history), 1)

    def test_checkout_out_of_stock_rejection(self):
        # Attempt to order more than available stock (p2 has only 2 items)
        checkout_payload = {
            'customer_name': 'Bob Overbuyer',
            'customer_email': 'bob@example.com',
            'customer_phone': '555-9999',
            'shipping_address': '200 High St',
            'payment_method': 'Cash on Delivery',
            'items': [
                {'id': self.p2_id, 'quantity': 5}
            ]
        }

        resp = self.client.post('/api/checkout', json=checkout_payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('Insufficient stock', data['error'])

    def test_order_tracking_and_status_update(self):
        # Create an order first
        with app.app_context():
            order = Order(
                id="ORD-TEST01",
                customer_name="Charlie Brown",
                customer_email="charlie@peanuts.com",
                customer_phone="555-4321",
                shipping_address="Pumpkin Patch Ave",
                payment_method="Credit Card",
                total_amount=50.0,
                status="Placed"
            )
            item = OrderItem(
                order_id="ORD-TEST01",
                product_id=self.p1_id,
                product_name="Test Headphones",
                price_at_purchase=50.0,
                quantity=1,
                subtotal=50.0
            )
            hist = OrderStatusHistory(
                order_id="ORD-TEST01",
                status="Placed",
                notes="Initial order placement."
            )
            db.session.add_all([order, item, hist])
            db.session.commit()

        # Track order view
        resp_track = self.client.get('/track/ORD-TEST01')
        self.assertEqual(resp_track.status_code, 200)
        self.assertIn(b'ORD-TEST01', resp_track.data)
        self.assertIn(b'Placed', resp_track.data)

        # Admin updates order status to Shipped
        resp_update = self.client.post('/admin/orders/ORD-TEST01/status', data={
            'status': 'Shipped',
            'notes': 'Handed over to carrier FedEx (Tracking #FX123456)'
        }, follow_redirects=True)
        self.assertEqual(resp_update.status_code, 200)

        with app.app_context():
            updated_order = db.session.get(Order, "ORD-TEST01")
            self.assertEqual(updated_order.status, 'Shipped')
            self.assertEqual(len(updated_order.history), 2)
            self.assertEqual(updated_order.history[1].status, 'Shipped')
            self.assertIn('FedEx', updated_order.history[1].notes)

        # Re-check tracking view shows updated status and history
        resp_track_after = self.client.get('/track/ORD-TEST01')
        self.assertEqual(resp_track_after.status_code, 200)
        self.assertIn(b'Shipped', resp_track_after.data)
        self.assertIn(b'FedEx', resp_track_after.data)

if __name__ == '__main__':
    unittest.main()
