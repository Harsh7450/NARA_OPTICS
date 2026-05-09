from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db
from models import Product, Order, OrderItem
from functools import wraps
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize database
init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Authentication Routes
@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Hash password and create user
        hashed_password = generate_password_hash(data['password'])
        cursor.execute('''
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        ''', (data['name'], data['email'], hashed_password))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (data['email'],))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[3], data['password']):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM orders 
        WHERE customer_email = ? 
        ORDER BY created_at DESC
    ''', (session['user_email'],))
    orders = cursor.fetchall()
    return render_template('account.html', orders=orders)

# Existing routes...
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE stock > 0')
    products = cursor.fetchall()
    return render_template('products.html', products=products)

@app.route('/api/products')
def api_products():
    db = get_db()
    cursor = db.cursor()
    category = request.args.get('category', 'all')
    
    if category == 'all':
        cursor.execute('SELECT * FROM products WHERE stock > 0')
    else:
        cursor.execute('SELECT * FROM products WHERE category = ? AND stock > 0', (category,))
    
    products = cursor.fetchall()
    products_list = []
    for p in products:
        products_list.append({
            'id': p[0],
            'name': p[1],
            'description': p[2],
            'price': p[3],
            'category': p[4],
            'image_url': p[5],
            'stock': p[6]
        })
    return jsonify(products_list)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if not product:
        return render_template('404.html'), 404
    return render_template('product_detail.html', product=product)

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if 'cart' not in session:
            session['cart'] = {}
        
        cart = session['cart']
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str] += quantity
        else:
            cart[product_id_str] = quantity
        
        session['cart'] = cart
        session.modified = True
        return jsonify({'success': True, 'cart_count': sum(cart.values())})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/cart')
def get_cart():
    if 'cart' not in session or not session['cart']:
        return jsonify({'items': [], 'total': 0})
    
    db = get_db()
    cursor = db.cursor()
    cart = session['cart']
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        if product:
            item_total = product[3] * quantity
            total += item_total
            cart_items.append({
                'id': product[0],
                'name': product[1],
                'price': product[3],
                'quantity': quantity,
                'image_url': product[5],
                'subtotal': item_total
            })
    
    return jsonify({'items': cart_items, 'total': total})

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        product_id_str = str(product_id)
        if product_id_str in cart:
            del cart[product_id_str]
            session['cart'] = cart
            session.modified = True
    return jsonify({'success': True})

@app.route('/api/order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        if 'cart' not in session or not session['cart']:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Calculate total
        cart = session['cart']
        total = 0
        for product_id, quantity in cart.items():
            cursor.execute('SELECT price, stock FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            if not product or product[1] < quantity:
                return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
            total += product[0] * quantity
        
        # Create order
        user_id = session.get('user_id')
        cursor.execute('''
            INSERT INTO orders (user_id, customer_name, customer_email, customer_phone, 
                               customer_address, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, data['name'], data['email'], data['phone'], 
              data['address'], total, 'pending'))
        
        order_id = cursor.lastrowid
        
        # Create order items and update stock
        for product_id, quantity in cart.items():
            cursor.execute('SELECT price FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, product_id, quantity, product[0]))
            
            # Update stock
            cursor.execute('''
                UPDATE products SET stock = stock - ? WHERE id = ?
            ''', (quantity, product_id))
        
        db.commit()
        session.pop('cart', None)
        
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search')
def search():
    query = request.args.get('q', '')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM products 
        WHERE name LIKE ? OR description LIKE ?
        AND stock > 0
    ''', (f'%{query}%', f'%{query}%'))
    products = cursor.fetchall()
    return render_template('search.html', products=products, query=query)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)