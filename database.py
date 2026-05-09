import sqlite3
from flask import g

DATABASE = 'nara_optics.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_url TEXT,
            stock INTEGER DEFAULT 0
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT,
            customer_address TEXT,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create order_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert sample products
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Ray-Ban Aviator Classic', 'Iconic gold-frame aviator sunglasses with crystal green lenses', 189.99, 'sunglasses', 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=500', 15),
            ('Oakley Holbrook', 'Timeless classic design fused with modern technology', 156.00, 'sunglasses', 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500', 20),
            ('Tom Ford FT5401', 'Sophisticated square optical frames in classic black', 435.00, 'eyeglasses', 'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?w=500', 10),
            ('Gucci GG0061O', 'Luxury round frames with iconic Gucci branding', 390.00, 'eyeglasses', 'https://images.unsplash.com/photo-1577803645773-f96470509666?w=500', 8),
            ('Prada PR 17WS', 'Contemporary cat-eye sunglasses', 340.00, 'sunglasses', 'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=500', 12),
            ('Persol PO3186S', 'Vintage-inspired round sunglasses', 299.00, 'sunglasses', 'https://images.unsplash.com/photo-1508296695146-257a814070b4?w=500', 18),
            ('Versace VE3270', 'Bold rectangular frames with Medusa detail', 275.00, 'eyeglasses', 'https://images.unsplash.com/photo-1483412468200-72182dbbc544?w=500', 14),
            ('Burberry BE2299', 'Classic check-detailed optical frames', 245.00, 'eyeglasses', 'https://images.unsplash.com/photo-1501466044931-62695aada8e9?w=500', 16),
        ]
        
        cursor.executemany('''
            INSERT INTO products (name, description, price, category, image_url, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_products)
    
    conn.commit()
    conn.close()