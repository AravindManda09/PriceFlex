from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import json

from app import db
from models import (
    User, Product, Sale, Competitor, CompetitorPrice, 
    PriceHistory, PriceRecommendation
)
from price_optimizer import PriceOptimizer
from utils import get_date_range_data

def register_routes(app):
    price_optimizer = PriceOptimizer()
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            flash('Invalid email or password', 'danger')
            
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            company_name = request.form.get('company_name')
            business_type = request.form.get('business_type')
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return render_template('register.html')
                
            if User.query.filter_by(username=username).first():
                flash('Username already taken', 'danger')
                return render_template('register.html')
            
            # Create new user
            user = User(
                username=username,
                email=email,
                company_name=company_name,
                business_type=business_type
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get products with recommendations
        products = Product.query.filter_by(user_id=current_user.id).all()
        product_count = len(products)
        
        # Get recent recommendations
        recommendations = PriceRecommendation.query.join(Product).filter(
            Product.user_id == current_user.id
        ).order_by(PriceRecommendation.created_at.desc()).limit(5).all()
        
        # Get sales data for charts
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sales = Sale.query.join(Product).filter(
            Product.user_id == current_user.id,
            Sale.sale_date >= thirty_days_ago
        ).all()
        
        # Prepare daily sales data
        daily_sales = get_date_range_data(sales, 'sale_date', 30)
        
        # Get competitor prices
        competitor_prices = CompetitorPrice.query.join(
            Product
        ).filter(
            Product.user_id == current_user.id
        ).order_by(CompetitorPrice.date_recorded.desc()).limit(50).all()
        
        # Calculate stats
        total_revenue = sum(sale.revenue for sale in sales)
        avg_price = sum(product.current_price for product in products) / max(product_count, 1)
        recommendation_count = PriceRecommendation.query.join(
            Product
        ).filter(
            Product.user_id == current_user.id
        ).count()
        
        return render_template(
            'dashboard.html',
            products=products,
            product_count=product_count,
            recommendations=recommendations,
            daily_sales=daily_sales,
            total_revenue=total_revenue,
            avg_price=avg_price,
            recommendation_count=recommendation_count
        )
    
    @app.route('/products')
    @login_required
    def products():
        products = Product.query.filter_by(user_id=current_user.id).all()
        return render_template('products.html', products=products)
    
    @app.route('/products/add', methods=['GET', 'POST'])
    @login_required
    def add_product():
        if request.method == 'POST':
            name = request.form.get('name')
            category = request.form.get('category')
            description = request.form.get('description')
            cost_price = float(request.form.get('cost_price'))
            current_price = float(request.form.get('current_price'))
            minimum_price = request.form.get('minimum_price')
            maximum_price = request.form.get('maximum_price')
            stock_level = int(request.form.get('stock_level') or 0)
            
            # Validate minimum price
            if minimum_price:
                minimum_price = float(minimum_price)
                if minimum_price > current_price:
                    flash('Minimum price cannot be greater than current price', 'danger')
                    return redirect(url_for('add_product'))
            
            # Validate maximum price
            if maximum_price:
                maximum_price = float(maximum_price)
                if maximum_price < current_price:
                    flash('Maximum price cannot be less than current price', 'danger')
                    return redirect(url_for('add_product'))
            
            # Create new product
            product = Product(
                name=name,
                category=category,
                description=description,
                cost_price=cost_price,
                current_price=current_price,
                minimum_price=minimum_price,
                maximum_price=maximum_price,
                stock_level=stock_level,
                user_id=current_user.id
            )
            
            db.session.add(product)
            db.session.commit()
            
            # Create initial price history entry
            price_history = PriceHistory(
                product_id=product.id,
                price=current_price
            )
            db.session.add(price_history)
            db.session.commit()
            
            flash('Product added successfully', 'success')
            return redirect(url_for('products'))
            
        return render_template('products.html', add_mode=True)
    
    @app.route('/products/<int:product_id>')
    @login_required
    def product_detail(product_id):
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Get sales data
        sales = Sale.query.filter_by(product_id=product.id).order_by(Sale.sale_date.desc()).limit(30).all()
        
        # Get price history
        price_history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.date_changed).all()
        
        # Get competitor prices
        competitor_prices = CompetitorPrice.query.filter_by(product_id=product.id).order_by(CompetitorPrice.date_recorded.desc()).all()
        
        # Get price recommendations
        recommendations = PriceRecommendation.query.filter_by(product_id=product.id).order_by(PriceRecommendation.created_at.desc()).limit(5).all()
        
        return render_template(
            'product_detail.html',
            product=product,
            sales=sales,
            price_history=price_history,
            competitor_prices=competitor_prices,
            recommendations=recommendations
        )
    
    @app.route('/products/<int:product_id>/recommend', methods=['POST'])
    @login_required
    def generate_recommendation(product_id):
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Get required data
        sales = Sale.query.filter_by(product_id=product.id).all()
        competitor_prices = CompetitorPrice.query.filter_by(product_id=product.id).all()
        price_history = PriceHistory.query.filter_by(product_id=product.id).all()
        
        # Generate recommendation
        recommendation_data = price_optimizer.optimize_price(
            product, sales, competitor_prices, price_history
        )
        
        # Save recommendation
        recommendation = PriceRecommendation(
            product_id=product.id,
            recommended_price=recommendation_data['recommended_price'],
            current_price=recommendation_data['current_price'],
            potential_revenue_increase=recommendation_data['potential_revenue_increase'],
            rationale=recommendation_data['rationale'],
            factors=recommendation_data['factors']
        )
        
        db.session.add(recommendation)
        db.session.commit()
        
        flash('New price recommendation generated', 'success')
        return redirect(url_for('product_detail', product_id=product.id))
    
    @app.route('/products/<int:product_id>/update_price', methods=['POST'])
    @login_required
    def update_price(product_id):
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        new_price = float(request.form.get('new_price'))
        recommendation_id = request.form.get('recommendation_id')
        
        # Update product price
        old_price = product.current_price
        product.current_price = new_price
        
        # Create price history entry
        price_history = PriceHistory(
            product_id=product.id,
            price=new_price
        )
        
        # If recommendation ID provided, update its status
        if recommendation_id:
            recommendation = PriceRecommendation.query.get(recommendation_id)
            if recommendation and recommendation.product_id == product.id:
                recommendation.status = 'accepted'
        
        db.session.add(price_history)
        db.session.commit()
        
        flash(f'Price updated from ${old_price:.2f} to ${new_price:.2f}', 'success')
        return redirect(url_for('product_detail', product_id=product.id))
    
    @app.route('/products/<int:product_id>/add_sale', methods=['POST'])
    @login_required
    def add_sale(product_id):
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        quantity = int(request.form.get('quantity'))
        price = float(request.form.get('price'))
        sale_date_str = request.form.get('sale_date')
        
        if sale_date_str:
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')
        else:
            sale_date = datetime.utcnow()
        
        # Create new sale
        sale = Sale(
            product_id=product.id,
            quantity=quantity,
            price=price,
            sale_date=sale_date
        )
        
        # Update stock level
        if product.stock_level is not None:
            product.stock_level = max(0, product.stock_level - quantity)
        
        db.session.add(sale)
        db.session.commit()
        
        flash(f'Sale of {quantity} units added successfully', 'success')
        return redirect(url_for('product_detail', product_id=product.id))
    
    @app.route('/competitors')
    @login_required
    def competitors():
        competitors = Competitor.query.filter_by(user_id=current_user.id).all()
        return render_template('competitors.html', competitors=competitors)
    
    @app.route('/competitors/add', methods=['GET', 'POST'])
    @login_required
    def add_competitor():
        if request.method == 'POST':
            name = request.form.get('name')
            website = request.form.get('website')
            notes = request.form.get('notes')
            
            # Create new competitor
            competitor = Competitor(
                name=name,
                website=website,
                notes=notes,
                user_id=current_user.id
            )
            
            db.session.add(competitor)
            db.session.commit()
            
            flash('Competitor added successfully', 'success')
            return redirect(url_for('competitors'))
            
        return render_template('competitors.html', add_mode=True)
    
    @app.route('/competitors/<int:competitor_id>/add_price', methods=['POST'])
    @login_required
    def add_competitor_price(competitor_id):
        competitor = Competitor.query.filter_by(id=competitor_id, user_id=current_user.id).first_or_404()
        
        product_id = request.form.get('product_id')
        price = float(request.form.get('price'))
        
        # Create new competitor price
        competitor_price = CompetitorPrice(
            product_id=product_id,
            competitor_id=competitor.id,
            price=price
        )
        
        db.session.add(competitor_price)
        db.session.commit()
        
        flash('Competitor price added successfully', 'success')
        return redirect(url_for('competitors'))
    
    @app.route('/api/product_data/<int:product_id>')
    @login_required
    def api_product_data(product_id):
        product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        # Get price history
        price_history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.date_changed).all()
        price_history_data = [
            {
                'date': ph.date_changed.strftime('%Y-%m-%d'),
                'price': ph.price
            }
            for ph in price_history
        ]
        
        # Get sales data
        sales = Sale.query.filter_by(product_id=product.id).order_by(Sale.sale_date).all()
        sales_data = [
            {
                'date': sale.sale_date.strftime('%Y-%m-%d'),
                'quantity': sale.quantity,
                'price': sale.price,
                'revenue': sale.revenue
            }
            for sale in sales
        ]
        
        # Get competitor prices
        competitor_prices = CompetitorPrice.query.filter_by(product_id=product.id).order_by(CompetitorPrice.date_recorded).all()
        competitor_price_data = [
            {
                'date': cp.date_recorded.strftime('%Y-%m-%d'),
                'competitor_id': cp.competitor_id,
                'competitor_name': Competitor.query.get(cp.competitor_id).name,
                'price': cp.price
            }
            for cp in competitor_prices
        ]
        
        return jsonify({
            'price_history': price_history_data,
            'sales': sales_data,
            'competitor_prices': competitor_price_data
        })
        
    @app.route('/api/dashboard_data')
    @login_required
    def api_dashboard_data():
        # Get date range
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sales data
        sales = Sale.query.join(Product).filter(
            Product.user_id == current_user.id,
            Sale.sale_date >= start_date
        ).all()
        
        # Prepare daily sales data
        daily_sales = get_date_range_data(sales, 'sale_date', days)
        
        # Get price changes
        price_changes = PriceHistory.query.join(Product).filter(
            Product.user_id == current_user.id,
            PriceHistory.date_changed >= start_date
        ).all()
        
        # Group price changes by date
        price_changes_by_date = {}
        for pc in price_changes:
            date_str = pc.date_changed.strftime('%Y-%m-%d')
            if date_str not in price_changes_by_date:
                price_changes_by_date[date_str] = 0
            price_changes_by_date[date_str] += 1
        
        price_change_data = [
            {
                'date': date,
                'count': count
            }
            for date, count in price_changes_by_date.items()
        ]
        
        return jsonify({
            'daily_sales': daily_sales,
            'price_changes': price_change_data
        })
    
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html')
    
    @app.route('/settings/update', methods=['POST'])
    @login_required
    def update_settings():
        user = current_user
        
        # Update user information
        user.company_name = request.form.get('company_name')
        user.business_type = request.form.get('business_type')
        
        db.session.commit()
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
    
    @app.route('/settings/change_password', methods=['POST'])
    @login_required
    def change_password():
        user = current_user
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('settings'))
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('settings'))
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('settings'))
