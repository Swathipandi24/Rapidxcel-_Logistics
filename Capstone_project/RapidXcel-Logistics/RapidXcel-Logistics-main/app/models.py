from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.username}>"

class Stock(db.Model):
    __tablename__ = 'stocks'

    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    
    def __repr__(self):
        return f"<Stock {self.stock_name}>"

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, nullable=False)
    grand_total = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.String(300), nullable=False)
    pincode = db.Column(db.String(6), nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default="Processing", nullable=False)

    customer = db.relationship('User', backref='customer_orders')
    items = db.relationship('OrderItem', backref='order_items', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.id}, Status: {self.status}, Customer: {self.customer.name}>"

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

    stock = db.relationship('Stock', backref='stock_orders')

    def __repr__(self):
        return f"{self.stock.stock_name} - {self.quantity}"
