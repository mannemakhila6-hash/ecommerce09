from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(60), nullable=False, default='General')
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'stock_quantity': self.stock_quantity,
            'image_url': self.image_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.String(32), primary_key=True)  # e.g., ORD-7B89F2
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default='Credit / Debit Card')
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(40), nullable=False, default='Placed')
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)
    history = db.relationship('OrderStatusHistory', backref='order', cascade='all, delete-orphan', order_by='OrderStatusHistory.timestamp.asc()', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%b %d, %Y %I:%M %p') if self.updated_at else '',
            'items': [item.to_dict() for item in self.items],
            'history': [h.to_dict() for h in self.history]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(32), db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'price_at_purchase': self.price_at_purchase,
            'quantity': self.quantity,
            'subtotal': self.subtotal
        }


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(32), db.ForeignKey('orders.id'), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'status': self.status,
            'notes': self.notes or '',
            'timestamp': self.timestamp.strftime('%b %d, %Y %I:%M %p') if self.timestamp else ''
        }
