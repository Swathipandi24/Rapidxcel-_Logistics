from flask import Blueprint, jsonify, render_template, request, redirect, session, url_for, flash, abort
from app import db
from app.models import Stock, User, Order, OrderItem
from flask_login import current_user, login_user, login_required, logout_user
from email_validator import validate_email, EmailNotValidError
from functools import wraps
from app.extensions import format_currency, calculate_shipping_cost, is_pincode_valid
import logging

auth_bp = Blueprint('auth', __name__)
inventory_bp = Blueprint('inventory', __name__)
order_bp = Blueprint('order', __name__)
courier_bp = Blueprint('courier', __name__)
logging.basicConfig(level=logging.DEBUG)

# Role-based access control decorator
def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Main Page Route
@auth_bp.route('/')
def index():
    return render_template('index.html')

# Register Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        role = request.form['role']

        try: 
            valid = validate_email(username) 
            username = valid.email 
        except EmailNotValidError as e: 
            flash(str(e), 'danger') 
            return redirect(url_for('auth.register')) 
        
        existing_user = User.query.filter_by(username=username).first() 
        if existing_user: 
            flash('Username already exists', 'danger') 
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        new_user.name = name

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful!', 'success')
        login_user(new_user)

        # Redirect based on user role
        if role == 'Inventory Manager':
            return redirect(url_for('auth.inventory'))
        elif role == 'Customer':
            return redirect(url_for('auth.customer_orders'))
        elif role == 'Supplier':
            return redirect(url_for('auth.supplier_monitor'))
        elif role == 'Courier Service':
            return redirect(url_for('auth.courier_dashboard'))

    return render_template('register.html')


# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            flash('Login successful!', 'success')
            login_user(user)

            # Redirect based on user role
            if user.role == 'Inventory Manager':
                return redirect(url_for('auth.inventory'))
            elif user.role == 'Customer':
                return redirect(url_for('auth.customer_orders'))
            elif user.role == 'Supplier':
                return redirect(url_for('auth.supplier_monitor'))
            elif user.role == 'Courier Service':
                return redirect(url_for('auth.courier_dashboard'))
            else: 
                flash('Role not recognized, redirecting to the main page.', 'info')
                return redirect(url_for('auth.index'))

        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.index'))

@auth_bp.route('/customer_orders')
@role_required('Customer')
def customer_orders():
    # Fetch available products from the database
    products = Stock.query.all()
    logging.debug(f'Products: {products}')

    # Fetch the user's current cart
    cart = session.get('cart', [])
    total_cost = sum(item['total_price'] for item in cart)
    shipping_cost = calculate_shipping_cost(cart)
    grand_total = total_cost + shipping_cost

    return render_template(
        'customer_orders.html',
        products=products,
        cart=cart,
        total_cost=total_cost,
        shipping_cost=shipping_cost,
        grand_total=grand_total
    )

@auth_bp.route('/inventory')
@role_required('Inventory Manager')
def inventory():
    low_stock_threshold = 10
    stocks = Stock.query.all()
    for stock in stocks:
        if stock.quantity < low_stock_threshold:
            flash(f'Stock for {stock.stock_name} is low!', 'warning')
        stock.formatted_price = format_currency(stock.price)  # Set an instance attribute
    return render_template('inventory.html', stocks=stocks)

@auth_bp.route('/supplier_monitor')
@role_required('Supplier')
def supplier_monitor():
    return render_template('supplier_monitor.html')

# @auth_bp.route('/courier_shipments')
# @role_required('Courier Service')   
# def courier_shipments():
#     return render_template('courier_shipments.html')

@inventory_bp.route('/inventory', methods=['GET'])
@login_required
def inventory_list():
    stocks = Stock.query.all()
    return render_template('inventory.html', stocks=stocks)

# Add new stock
@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_stock():
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            unit = request.form['unit']

            if not all([request.form['stock_name'], request.form['price'], request.form['quantity'], weight, unit]):
                flash('All fields are required!', 'danger')
                return redirect('/inventory/add')

            new_stock = Stock(
                stock_name=request.form['stock_name'],
                price=float(request.form['price']),
                quantity=int(request.form['quantity']),
                weight=weight,
                unit=unit
            )
            db.session.add(new_stock)
            db.session.commit()
            flash('Stock added successfully!', 'success')
        except ValueError:
            flash('Please enter valid data for all fields.', 'danger')

        return redirect('/inventory')

    return render_template('inventory/add_stock.html')

# Update stock
@inventory_bp.route('/inventory/edit/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def edit_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            unit = request.form['unit']
            
            if not all([request.form['stock_name'], request.form['price'], request.form['quantity'], weight, unit]):
                flash('All fields are required!', 'danger')
                return redirect(url_for('inventory.edit_stock', stock_id=stock_id))

            stock.stock_name = request.form['stock_name']
            stock.price = float(request.form['price'])
            stock.quantity = int(request.form['quantity'])
            stock.weight = weight
            stock.unit = unit

            db.session.commit()
            flash('Stock updated successfully!', 'success')
        except ValueError:
            flash('Please enter valid data for all fields.', 'danger')

        return redirect(url_for('inventory.inventory_list'))

    return render_template('inventory/edit_stock.html', stock=stock)


# Delete stock
@inventory_bp.route('/inventory/delete/<int:stock_id>', methods=['POST'])
@login_required
def delete_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    flash('Stock deleted successfully!', 'success')
    return redirect(url_for('inventory.inventory_list'))

@order_bp.route('/add_to_cart', methods=['POST'])
@role_required('Customer')
def add_to_cart():
    product_ids = request.form.getlist('product_ids[]')
    quantities = request.form.getlist('quantities[]')

    cart = session.get('cart', [])

    for product_id, quantity in zip(product_ids, quantities):
        if not quantity:
            continue

        product_id = int(product_id)
        quantity = int(quantity)

        # Fetch product details from the database
        product = Stock.query.get_or_404(product_id)
        if quantity > product.quantity:
            flash(f'Insufficient stock for {product.stock_name}.', 'danger')
            continue

        # Add to session-based cart
        cart.append({
            'product_id': product_id,
            'product_name': product.stock_name,
            'quantity': quantity,
            'total_price': product.price * quantity
        })

    session['cart'] = cart
    flash('Products added to your cart.', 'success')
    return redirect(url_for('order.order_review_page'))

@order_bp.route('/place_order', methods=['POST'])
@role_required('Customer')
def place_order():
    address = request.form['address']
    pincode = request.form['pincode']
    phone = request.form['phone']

    if not is_pincode_valid(pincode):
        flash('Invalid or unserviceable pin code.', 'danger')
        return redirect(url_for('auth.customer_orders'))

    cart = session.get('cart', [])
    total_cost = sum(item['total_price'] for item in cart)
    shipping_cost = calculate_shipping_cost(cart)
    grand_total = total_cost + shipping_cost

    new_order = Order(
        customer_id=current_user.id,
        delivery_address=address,
        pincode=pincode,
        phone=phone,
        total_cost=total_cost,
        shipping_cost=shipping_cost,
        grand_total=grand_total
    )

    db.session.add(new_order)
    db.session.commit()

    for item in cart:
        order_item = OrderItem(
            order_id=new_order.id,
            stock_id=item['product_id'],
            quantity=item['quantity'],
            weight=0,  
            unit='' 
        )
        db.session.add(order_item)

        product = Stock.query.get(item['product_id'])
        if product:
            product.quantity -= item['quantity']
            db.session.add(product)

    db.session.commit()
    session.pop('cart', None)
    return render_template('orders/order_confirmation.html', order=new_order, items=cart)

@order_bp.route('/place_order_page')
@role_required('Customer')
def place_order_page():
    products = Stock.query.all()
    return render_template('orders/place_order.html', products=products)

@order_bp.route('/order_history')
@role_required('Customer')
def order_history():
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    return render_template('orders/order_history.html', orders=orders)

@order_bp.route('/order_details/<int:order_id>')
@role_required('Customer')
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        abort(403)
    return render_template('orders/order_details.html', order=order)

@order_bp.route('/order_review_page')
@role_required('Customer')
def order_review_page():
    cart = session.get('cart', [])
    total_cost = sum(item['total_price'] for item in cart)
    shipping_cost = calculate_shipping_cost(cart)
    grand_total = total_cost + shipping_cost
    return render_template('orders/order_review.html', cart=cart, total_cost=total_cost, shipping_cost=shipping_cost, grand_total=grand_total)

@auth_bp.route('/courier_shipments')
@role_required('Courier Service')
def courier_dashboard():
    orders = Order.query.all()
    return render_template('courier/dashboard.html', orders=orders)

@courier_bp.route('/update_status/<int:order_id>', methods=['POST'])
@role_required('Courier Service')
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form['status']
    order.status = new_status
    db.session.commit()
    flash('Order status updated successfully!', 'success')
    return redirect(url_for('auth.courier_dashboard'))

@courier_bp.route('/track_delivery/<int:order_id>')
@role_required('Customer')
def track_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        abort(403)
    return render_template('courier/track_delivery.html', order=order)
