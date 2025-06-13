import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import json

class PriceOptimizer:
    """
    AI-based price optimization system that generates price recommendations 
    based on historical sales, competitor pricing, and stock levels.
    """
    def __init__(self):
        self.models = {}
        self.features = [
            'price_history_avg', 
            'price_history_trend',
            'competitor_price_avg', 
            'competitor_price_diff', 
            'sales_velocity', 
            'stock_ratio',
            'days_since_last_change'
        ]
        
    def prepare_features(self, product, sales, competitor_prices, price_history):
        features = {}
        
        # Process price history
        if price_history:
            prices = [ph.price for ph in price_history]
            features['price_history_avg'] = sum(prices) / len(prices)
            if len(prices) > 1:
                features['price_history_trend'] = (prices[-1] - prices[0]) / prices[0]
            else:
                features['price_history_trend'] = 0
            last_change_date = max([ph.date_changed for ph in price_history])
            features['days_since_last_change'] = (datetime.utcnow() - last_change_date).days
        else:
            features['price_history_avg'] = product.current_price
            features['price_history_trend'] = 0
            features['days_since_last_change'] = 30
        
        # Competitor pricing
        if competitor_prices:
            comp_prices = [cp.price for cp in competitor_prices]
            features['competitor_price_avg'] = sum(comp_prices) / len(comp_prices)
            features['competitor_price_diff'] = product.current_price - features['competitor_price_avg']
        else:
            features['competitor_price_avg'] = product.current_price
            features['competitor_price_diff'] = 0
            
        # Sales data
        if sales:
            recent_sales = [s for s in sales if s.sale_date > datetime.utcnow() - timedelta(days=30)]
            if recent_sales:
                features['sales_velocity'] = len(recent_sales) / 30
                if len(recent_sales) >= 5:
                    try:
                        df = pd.DataFrame([(s.price, s.quantity) for s in recent_sales], 
                                         columns=['price', 'quantity'])
                        log_prices = np.log(df['price'])
                        log_quantities = np.log(df['quantity'])
                        if len(log_prices) > 1 and len(log_quantities) > 1:
                            model = LinearRegression()
                            model.fit(log_prices.values.reshape(-1, 1), log_quantities)
                            features['price_elasticity'] = model.coef_[0]
                        else:
                            features['price_elasticity'] = -1.0
                    except:
                        features['price_elasticity'] = -1.0
                else:
                    features['price_elasticity'] = -1.0
            else:
                features['sales_velocity'] = 0
                features['price_elasticity'] = -1.0
        else:
            features['sales_velocity'] = 0
            features['price_elasticity'] = -1.0
        
        # Stock level
        if product.stock_level > 0:
            features['stock_ratio'] = product.stock_level / (features['sales_velocity'] + 0.1)
        else:
            features['stock_ratio'] = 0
            
        return features
        
    def optimize_price(self, product, sales, competitor_prices, price_history):
        features = self.prepare_features(product, sales, competitor_prices, price_history)
        
        recommendation = {}
        current_price = product.current_price
        recommended_price = current_price
        rationale = []
        factors_influence = {}
        
        # Competitor pricing influence
        if features['competitor_price_diff'] > 0:
            competitor_adjustment = -min(features['competitor_price_diff'] * 0.15, current_price * 0.05)
            recommended_price += competitor_adjustment
            rationale.append(f"Your price is higher than competitors by ₹{features['competitor_price_diff']:.2f}")
            factors_influence['competitor_pricing'] = -2
        elif features['competitor_price_diff'] < -5:
            competitor_adjustment = min(-features['competitor_price_diff'] * 0.1, current_price * 0.03)
            recommended_price += competitor_adjustment
            rationale.append(f"Your price is significantly lower than competitors by ₹{-features['competitor_price_diff']:.2f}")
            factors_influence['competitor_pricing'] = 2
        else:
            factors_influence['competitor_pricing'] = 0
        
        # Stock level influence
        if features['stock_ratio'] > 3:
            stock_adjustment = -min(current_price * 0.03, 3.0)
            recommended_price += stock_adjustment
            rationale.append("You have high inventory levels relative to sales velocity")
            factors_influence['inventory_level'] = -2
        elif features['stock_ratio'] < 0.5:
            stock_adjustment = min(current_price * 0.02, 2.0)
            recommended_price += stock_adjustment
            rationale.append("Your inventory is running low relative to sales velocity")
            factors_influence['inventory_level'] = 2
        else:
            factors_influence['inventory_level'] = 0
        
        # Sales velocity influence
        if features['sales_velocity'] > 1:
            velocity_adjustment = min(current_price * 0.02, 2.0)
            recommended_price += velocity_adjustment
            rationale.append(f"Your product is selling well with {features['sales_velocity']:.2f} units per day")
            factors_influence['sales_performance'] = 2
        elif features['sales_velocity'] < 0.2 and features['sales_velocity'] > 0:
            velocity_adjustment = -min(current_price * 0.04, 4.0)
            recommended_price += velocity_adjustment
            rationale.append(f"Sales are slow with only {features['sales_velocity']:.2f} units per day")
            factors_influence['sales_performance'] = -2
        else:
            factors_influence['sales_performance'] = 0
        
        # Price staleness
        if features['days_since_last_change'] > 45:
            staleness_adjustment = current_price * 0.01
            if features['price_history_trend'] >= 0:
                recommended_price += staleness_adjustment
                rationale.append(f"Price hasn't been updated in {features['days_since_last_change']} days and trend is upward")
            else:
                recommended_price -= staleness_adjustment
                rationale.append(f"Price hasn't been updated in {features['days_since_last_change']} days and trend is downward")
            factors_influence['price_freshness'] = 1
        else:
            factors_influence['price_freshness'] = 0
            
        # Apply constraints
        if product.minimum_price and recommended_price < product.minimum_price:
            recommended_price = product.minimum_price
            rationale.append(f"Price adjusted to respect your minimum price threshold (₹{product.minimum_price:.2f})")
            
        if product.maximum_price and recommended_price > product.maximum_price:
            recommended_price = product.maximum_price
            rationale.append(f"Price adjusted to respect your maximum price threshold (₹{product.maximum_price:.2f})")
        
        # Round to psychological price points
        recommended_price = float(recommended_price)
        if recommended_price >= 100:
            recommended_price = float(np.floor(recommended_price)) - 0.01
        elif recommended_price >= 10:
            recommended_price = float(np.floor(recommended_price * 2) / 2) - 0.01
        else:
            recommended_price = float(np.floor(recommended_price * 4) / 4) - 0.01
        
        # Avoid tiny changes
        if abs(recommended_price - current_price) < (current_price * 0.01):
            recommended_price = current_price
            rationale = ["Current price is optimal based on market conditions"]
        
        # Estimate revenue impact
        potential_revenue = 0
        if features['sales_velocity'] > 0 and 'price_elasticity' in features:
            price_change_ratio = float(recommended_price) / float(current_price)
            quantity_change_ratio = 1 + (float(features['price_elasticity']) * (price_change_ratio - 1))
            new_velocity = float(features['sales_velocity']) * quantity_change_ratio
            current_monthly_revenue = float(features['sales_velocity']) * 30 * float(current_price)
            new_monthly_revenue = float(new_velocity) * 30 * float(recommended_price)
            potential_revenue = float(new_monthly_revenue - current_monthly_revenue)
            
            if potential_revenue > 0:
                rationale.append(f"This change could increase monthly revenue by approximately ₹{potential_revenue:.2f}")
            else:
                rationale.append("This price optimizes for long-term market position despite a potential short-term revenue decrease")
        
        recommendation = {
            'product_id': int(product.id),
            'current_price': float(current_price),
            'recommended_price': float(round(float(recommended_price), 2)),
            'potential_revenue_increase': float(round(float(potential_revenue), 2)),
            'rationale': '. '.join(rationale),
            'factors': json.dumps(factors_influence)
        }
        
        return recommendation
