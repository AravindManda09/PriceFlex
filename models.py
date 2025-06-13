import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    company_name = db.Column(db.String(100))
    business_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    products = db.relationship('Product', backref='owner', lazy='dynamic')
    competitors = db.relationship('Competitor', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    cost_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    minimum_price = db.Column(db.Float)
    maximum_price = db.Column(db.Float)
    stock_level = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sales = db.relationship('Sale', backref='product', lazy='dynamic')
    competitor_prices = db.relationship('CompetitorPrice', backref='product', lazy='dynamic')
    price_histories = db.relationship('PriceHistory', backref='product', lazy='dynamic')
    price_recommendations = db.relationship('PriceRecommendation', backref='product', lazy='dynamic')


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    @property
    def revenue(self):
        return self.quantity * self.price


class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(255))
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prices = db.relationship('CompetitorPrice', backref='competitor', lazy='dynamic')


class CompetitorPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date_changed = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class PriceRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    recommended_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    potential_revenue_increase = db.Column(db.Float)
    rationale = db.Column(db.Text)
    factors = db.Column(db.Text)  # JSON string of factors influencing the recommendation
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
