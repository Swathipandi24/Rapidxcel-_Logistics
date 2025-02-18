# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def format_currency(value):
    """Format a number as Indian currency."""
    if value is None:
        return ''
    
    # Split the integer and decimal parts
    value = f"{value:.2f}"  # Ensure two decimal places
    integer_part, decimal_part = value.split('.')
    
    # Format the integer part for Indian numbering system
    last_three = integer_part[-3:]
    remaining = integer_part[:-3]
    if remaining:
        formatted_integer = f"{remaining},{last_three}"
    else:
        formatted_integer = last_three
    
    return f"₹{formatted_integer}.{decimal_part}"

def is_pincode_valid(pincode):
    serviceable_pincodes = ['600001', '600002', '600003']
    return pincode in serviceable_pincodes

def calculate_shipping_cost(cart):
    total_weight = sum(item['quantity'] for item in cart)
    base_cost = 50
    per_kg_cost = 10
    return base_cost + (total_weight * per_kg_cost)