from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import hashlib
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-2024'

DATA_FILE = 'data.json'
SALES_FILE = 'sales.json'
USERS_FILE = 'users.json'
CUSTOMERS_FILE = 'customers.json'
LOGS_FILE = 'activity_logs.json'

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(filepath, default):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default

def save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

def load_data():
    return load_json(DATA_FILE, {'items': [], 'last_id': 0})

def save_data(data):
    return save_json(DATA_FILE, data)

def load_sales():
    return load_json(SALES_FILE, {'sales': [], 'last_id': 0})

def save_sales(data):
    return save_json(SALES_FILE, data)

def load_users():
    return load_json(USERS_FILE, {'users': [], 'last_id': 0})

def save_users(data):
    return save_json(USERS_FILE, data)

def load_customers():
    return load_json(CUSTOMERS_FILE, {'customers': [], 'last_id': 0})

def save_customers(data):
    return save_json(CUSTOMERS_FILE, data)

def load_logs():
    return load_json(LOGS_FILE, {'logs': [], 'last_id': 0})

def save_logs(data):
    return save_json(LOGS_FILE, data)

def log_activity(action, details, item_info=''):
    logs_data = load_logs()
    logs_data['last_id'] += 1
    log = {
        'id': logs_data['last_id'],
        'user': session.get('username', 'Unknown'),
        'role': session.get('role', 'Unknown'),
        'action': action,
        'details': details,
        'item_info': item_info,
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    logs_data['logs'].append(log)
    # Keep last 500 logs
    if len(logs_data['logs']) > 500:
        logs_data['logs'] = logs_data['logs'][-500:]
    save_logs(logs_data)

def find_item_by_id(items, search_id):
    search_id_str = str(search_id).strip().upper()
    try:
        numeric_id = int(search_id)
        for item in items:
            if item.get('id') == numeric_id:
                return item
    except ValueError:
        pass
    for item in items:
        if str(item.get('unique_id', '')).upper() == search_id_str:
            return item
    return None

def require_login(func):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def require_admin(func):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def init_default_data():
    """Initialize default admin user if no users exist"""
    users_data = load_users()
    if not users_data['users']:
        users_data['last_id'] = 1
        users_data['users'] = [{
            'id': 1,
            'username': 'Admin',
            'password': hash_password('Admin123'),
            'role': 'admin',
            'name': 'Administrator',
            'email': 'admin@store.com',
            'created_at': datetime.now().isoformat(),
            'active': True
        }]
        save_users(users_data)
        print("✓ Default admin user created: Admin / Admin123")

# ============================================================
# AUTH ROUTES
# ============================================================

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    users_data = load_users()
    user = next((u for u in users_data['users']
                 if u['username'].lower() == username.lower()
                 and u['password'] == hash_password(password)
                 and u.get('active', True)), None)
    if user:
        session['logged_in'] = True
        session['username'] = user['username']
        session['role'] = user['role']
        session['user_id'] = user['id']
        session['name'] = user.get('name', user['username'])
        log_activity('LOGIN', f"User logged in")
        return jsonify({'success': True, 'role': user['role']})
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/logout')
def logout():
    if 'logged_in' in session:
        log_activity('LOGOUT', 'User logged out')
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html', username=session.get('name', 'User'), role=session.get('role'))

@app.route('/analytics')
def analytics():
    if 'logged_in' not in session:
        return redirect(url_for('login_page'))
    return render_template('analytics.html', username=session.get('name', 'User'), role=session.get('role'))

@app.route('/customers')
def customers_page():
    if 'logged_in' not in session:
        return redirect(url_for('login_page'))
    return render_template('customers.html', username=session.get('name', 'User'), role=session.get('role'))

@app.route('/invoice/<int:sale_id>')
def invoice_page(sale_id):
    if 'logged_in' not in session:
        return redirect(url_for('login_page'))
    return render_template('invoice.html', sale_id=sale_id, username=session.get('name', 'User'), role=session.get('role'))

@app.route('/admin/users')
def admin_users():
    if 'logged_in' not in session:
        return redirect(url_for('login_page'))
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin_users.html', username=session.get('name', 'User'), role=session.get('role'))

@app.route('/admin/logs')
def admin_logs():
    if 'logged_in' not in session:
        return redirect(url_for('login_page'))
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin_logs.html', username=session.get('name', 'User'), role=session.get('role'))

# ============================================================
# SESSION INFO
# ============================================================

@app.route('/api/session')
def get_session():
    if 'logged_in' not in session:
        return jsonify({'logged_in': False})
    return jsonify({
        'logged_in': True,
        'username': session.get('username'),
        'name': session.get('name'),
        'role': session.get('role')
    })

# ============================================================
# INVENTORY API
# ============================================================

@app.route('/api/items', methods=['GET'])
@require_login
def get_items():
    try:
        data = load_data()
        return jsonify({'success': True, 'data': data['items']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/items', methods=['POST'])
@require_admin
def add_item():
    try:
        data = load_data()
        new_item = request.get_json()
        data['last_id'] += 1
        new_item['id'] = data['last_id']
        letter_index = (data['last_id'] - 1) // 10
        number = ((data['last_id'] - 1) % 10) + 1
        letter = chr(65 + letter_index)
        new_item['unique_id'] = f"{letter}{number:02d}"
        if 'category' not in new_item:
            new_item['category'] = 'General'
        required = ['name', 'quantity', 'location', 'supplier', 'price']
        for field in required:
            if field not in new_item:
                return jsonify({'success': False, 'message': f'Missing {field}'}), 400
        data['items'].append(new_item)
        if save_data(data):
            log_activity('ADD_ITEM', f"Added item: {new_item['name']}", f"ID: {new_item['unique_id']}, Qty: {new_item['quantity']}, Price: ₹{new_item['price']}")
            return jsonify({'success': True, 'data': new_item}), 201
        return jsonify({'success': False, 'message': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['GET'])
@require_login
def get_item(item_id):
    try:
        data = load_data()
        item = find_item_by_id(data['items'], item_id)
        if item:
            return jsonify({'success': True, 'data': item})
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['PUT'])
@require_admin
def update_item(item_id):
    try:
        data = load_data()
        update_data = request.get_json()
        item = find_item_by_id(data['items'], item_id)
        if item:
            old_name = item['name']
            preserved_id = item['id']
            preserved_unique_id = item.get('unique_id', '')
            item.update(update_data)
            item['id'] = preserved_id
            if preserved_unique_id:
                item['unique_id'] = preserved_unique_id
            if save_data(data):
                log_activity('UPDATE_ITEM', f"Updated item: {old_name}", f"ID: {preserved_unique_id}")
                return jsonify({'success': True, 'data': item})
            return jsonify({'success': False, 'message': 'Failed to save'}), 500
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['DELETE'])
@require_admin
def delete_item(item_id):
    try:
        data = load_data()
        item = find_item_by_id(data['items'], item_id)
        if item:
            item_name = item['name']
            item_uid = item.get('unique_id', '')
            data['items'].remove(item)
            if save_data(data):
                log_activity('DELETE_ITEM', f"Deleted item: {item_name}", f"ID: {item_uid}")
                return jsonify({'success': True, 'message': 'Item deleted'})
            return jsonify({'success': False, 'message': 'Failed to save'}), 500
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search', methods=['GET'])
@require_login
def search_items():
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({'success': False, 'message': 'Empty search query'}), 400
        data = load_data()
        results = [item for item in data['items'] if
                   query in str(item.get('id', '')).lower() or
                   query in str(item.get('unique_id', '')).lower() or
                   query in item.get('name', '').lower() or
                   query in item.get('location', '').lower() or
                   query in item.get('supplier', '').lower() or
                   query in item.get('category', '').lower()]
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# SALES API
# ============================================================

@app.route('/api/sell', methods=['POST'])
@require_login
def record_sale():
    try:
        sale_input = request.get_json()
        item_id = sale_input.get('item_id')
        quantity = sale_input.get('quantity')
        selling_price = sale_input.get('selling_price')
        customer_id = sale_input.get('customer_id')
        customer_name = sale_input.get('customer_name', 'Walk-in Customer')
        customer_phone = sale_input.get('customer_phone', '')
        payment_method = sale_input.get('payment_method', 'Cash')
        notes = sale_input.get('notes', '')

        if not all([item_id, quantity, selling_price]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        data = load_data()
        item = find_item_by_id(data['items'], item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        if item['quantity'] < quantity:
            return jsonify({'success': False, 'message': 'Insufficient stock'}), 400

        cost_price = item['price']
        profit = (selling_price - cost_price) * quantity
        item['quantity'] -= quantity

        sales = load_sales()
        sales['last_id'] += 1

        sale_record = {
            'id': sales['last_id'],
            'item_id': item['id'],
            'unique_item_id': item.get('unique_id', ''),
            'item_name': item['name'],
            'category': item.get('category', 'General'),
            'quantity': quantity,
            'cost_price': cost_price,
            'selling_price': selling_price,
            'profit': profit,
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'payment_method': payment_method,
            'notes': notes,
            'recorded_by': session.get('username', 'Unknown'),
            'date': datetime.now().isoformat(),
            'month': datetime.now().strftime('%Y-%m')
        }

        sales['sales'].append(sale_record)

        if save_data(data) and save_sales(sales):
            log_activity('SALE', f"Sold {quantity}x {item['name']} to {customer_name}",
                        f"Sale ID: {sales['last_id']}, Revenue: ₹{selling_price*quantity:.2f}, Profit: ₹{profit:.2f}")
            return jsonify({'success': True, 'data': sale_record})
        return jsonify({'success': False, 'message': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sales', methods=['GET'])
@require_login
def get_sales():
    try:
        sales = load_sales()
        return jsonify({'success': True, 'data': sales['sales']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sales/<int:sale_id>', methods=['GET'])
@require_login
def get_sale(sale_id):
    try:
        sales = load_sales()
        sale = next((s for s in sales['sales'] if s['id'] == sale_id), None)
        if sale:
            return jsonify({'success': True, 'data': sale})
        return jsonify({'success': False, 'message': 'Sale not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# CUSTOMER API
# ============================================================

@app.route('/api/customers', methods=['GET'])
@require_login
def get_customers():
    try:
        customers = load_customers()
        return jsonify({'success': True, 'data': customers['customers']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customers', methods=['POST'])
@require_login
def add_customer():
    try:
        customers = load_customers()
        new_customer = request.get_json()
        customers['last_id'] += 1
        new_customer['id'] = customers['last_id']
        new_customer['created_at'] = datetime.now().isoformat()
        new_customer['created_by'] = session.get('username')
        if 'name' not in new_customer or not new_customer['name']:
            return jsonify({'success': False, 'message': 'Customer name is required'}), 400
        customers['customers'].append(new_customer)
        if save_customers(customers):
            log_activity('ADD_CUSTOMER', f"Added customer: {new_customer['name']}", f"Phone: {new_customer.get('phone', 'N/A')}")
            return jsonify({'success': True, 'data': new_customer}), 201
        return jsonify({'success': False, 'message': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
@require_login
def get_customer(customer_id):
    try:
        customers = load_customers()
        customer = next((c for c in customers['customers'] if c['id'] == customer_id), None)
        if customer:
            # Get customer's sales history
            sales = load_sales()
            customer_sales = [s for s in sales['sales'] if s.get('customer_id') == customer_id]
            total_spent = sum(s['selling_price'] * s['quantity'] for s in customer_sales)
            return jsonify({'success': True, 'data': customer, 'sales': customer_sales, 'total_spent': total_spent})
        return jsonify({'success': False, 'message': 'Customer not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@require_login
def update_customer(customer_id):
    try:
        customers = load_customers()
        update_data = request.get_json()
        customer = next((c for c in customers['customers'] if c['id'] == customer_id), None)
        if customer:
            old_name = customer['name']
            preserved_id = customer['id']
            customer.update(update_data)
            customer['id'] = preserved_id
            if save_customers(customers):
                log_activity('UPDATE_CUSTOMER', f"Updated customer: {old_name}")
                return jsonify({'success': True, 'data': customer})
        return jsonify({'success': False, 'message': 'Customer not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customers/search', methods=['GET'])
@require_login
def search_customers():
    try:
        query = request.args.get('q', '').strip().lower()
        customers = load_customers()
        if not query:
            return jsonify({'success': True, 'data': customers['customers']})
        results = [c for c in customers['customers'] if
                   query in c.get('name', '').lower() or
                   query in c.get('phone', '').lower() or
                   query in c.get('email', '').lower()]
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# INVOICE API
# ============================================================

@app.route('/api/invoice/<int:sale_id>', methods=['GET'])
@require_login
def get_invoice(sale_id):
    try:
        sales = load_sales()
        sale = next((s for s in sales['sales'] if s['id'] == sale_id), None)
        if not sale:
            return jsonify({'success': False, 'message': 'Sale not found'}), 404

        customer = None
        if sale.get('customer_id'):
            customers = load_customers()
            customer = next((c for c in customers['customers'] if c['id'] == sale['customer_id']), None)

        invoice = {
            'invoice_number': f"INV-{sale_id:05d}",
            'sale': sale,
            'customer': customer,
            'store_name': 'Mohit Enterprises',
            'store_address': 'Mahalwada road, Ratlam',
            'store_phone': '+91 65896 13425',
            'store_gst': 'GST: XXXXXXXXXXXXXXX',
            'generated_at': datetime.now().isoformat()
        }
        return jsonify({'success': True, 'data': invoice})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/invoices', methods=['GET'])
@require_login
def get_invoices():
    try:
        sales = load_sales()
        customers = load_customers()
        customers_map = {c['id']: c for c in customers['customers']}

        # Optional filters
        customer_id = request.args.get('customer_id', type=int)
        date_from = request.args.get('from')
        date_to = request.args.get('to')

        sales_list = sales['sales']
        if customer_id:
            sales_list = [s for s in sales_list if s.get('customer_id') == customer_id]
        if date_from:
            sales_list = [s for s in sales_list if s['date'][:10] >= date_from]
        if date_to:
            sales_list = [s for s in sales_list if s['date'][:10] <= date_to]

        invoices = []
        for s in sales_list:
            customer = customers_map.get(s.get('customer_id'), {})
            invoices.append({
                'invoice_number': f"INV-{s['id']:05d}",
                'sale_id': s['id'],
                'customer_name': s.get('customer_name', 'Walk-in Customer'),
                'customer_phone': s.get('customer_phone', ''),
                'item_name': s['item_name'],
                'quantity': s['quantity'],
                'amount': round(s['selling_price'] * s['quantity'], 2),
                'profit': round(s['profit'], 2),
                'payment_method': s.get('payment_method', 'Cash'),
                'date': s['date'],
                'recorded_by': s.get('recorded_by', 'Unknown')
            })

        invoices.sort(key=lambda x: x['date'], reverse=True)
        return jsonify({'success': True, 'data': invoices})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# ANALYTICS & FORECAST API
# ============================================================

@app.route('/api/analytics/forecast', methods=['GET'])
@app.route('/api/forecast', methods=['GET'])
@require_login
def get_forecast():
    try:
        mode = request.args.get('mode', 'normal')  # conservative, normal, aggressive
        multipliers = {'conservative': 1.2, 'normal': 1.5, 'aggressive': 2.0}
        multiplier = multipliers.get(mode, 1.5)

        data = load_data()
        sales_data = load_sales()
        items = data.get('items', [])
        sales = sales_data.get('sales', [])

        if not sales or not items:
            return jsonify({'success': True, 'data': []})

        # Group sales by item and month
        sales_by_item = defaultdict(lambda: {'monthly': defaultdict(int), 'total': 0})
        for sale in sales:
            item_id = sale.get('item_id')
            month = sale.get('month', '')
            qty = sale.get('quantity', 0)
            if item_id and month:
                sales_by_item[item_id]['monthly'][month] += qty
                sales_by_item[item_id]['total'] += qty

        forecast_data = []
        for item in items:
            item_id = item.get('id')
            if item_id in sales_by_item:
                monthly_data = sales_by_item[item_id]['monthly']
                # Sort months and take last 3 for moving average
                sorted_months = sorted(monthly_data.keys())
                last_3 = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months
                moving_avg = sum(monthly_data[m] for m in last_3) / len(last_3) if last_3 else 0

                recommended = int(moving_avg * multiplier)
                current_stock = item.get('quantity', 0)

                forecast_data.append({
                    'item_id': item_id,
                    'unique_id': item.get('unique_id', ''),
                    'item_name': item.get('name', ''),
                    'category': item.get('category', 'General'),
                    'current_stock': current_stock,
                    'avg_monthly_sales': round(moving_avg, 2),
                    'recommended_order': max(recommended, 1),
                    'status': 'reorder_needed' if current_stock < recommended else 'sufficient',
                    'months_analyzed': len(last_3)
                })

        return jsonify({'success': True, 'data': forecast_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
@require_login
def get_dashboard_analytics():
    try:
        sales_data = load_sales()
        sales = sales_data.get('sales', [])

        if not sales:
            return jsonify({'success': True, 'data': {
                'top_products': [], 'worst_products': [],
                'monthly_revenue': [], 'category_revenue': [],
                'total_revenue': 0, 'total_profit': 0
            }})

        # Product performance
        product_stats = defaultdict(lambda: {'revenue': 0, 'profit': 0, 'quantity': 0, 'category': 'General'})
        monthly_stats = defaultdict(lambda: {'revenue': 0, 'profit': 0})
        category_stats = defaultdict(lambda: {'revenue': 0, 'profit': 0})

        for sale in sales:
            name = sale.get('item_name', 'Unknown')
            cat = sale.get('category', 'General')
            revenue = sale.get('selling_price', 0) * sale.get('quantity', 0)
            profit = sale.get('profit', 0)
            month = sale.get('month', '')

            product_stats[name]['revenue'] += revenue
            product_stats[name]['profit'] += profit
            product_stats[name]['quantity'] += sale.get('quantity', 0)
            product_stats[name]['category'] = cat

            monthly_stats[month]['revenue'] += revenue
            monthly_stats[month]['profit'] += profit

            category_stats[cat]['revenue'] += revenue
            category_stats[cat]['profit'] += profit

        sorted_products = sorted(product_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)

        return jsonify({'success': True, 'data': {
            'top_products': [{'name': k, **v} for k, v in sorted_products[:5]],
            'worst_products': [{'name': k, **v} for k, v in sorted_products[-5:]],
            'monthly_revenue': [{'month': k, **v} for k, v in sorted(monthly_stats.items())],
            'category_revenue': [{'category': k, **v} for k, v in category_stats.items()],
            'total_revenue': round(sum(v['revenue'] for v in product_stats.values()), 2),
            'total_profit': round(sum(v['profit'] for v in product_stats.values()), 2)
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/analytics/product/<item_name>', methods=['GET'])
@require_login
def get_product_analytics(item_name):
    try:
        sales_data = load_sales()
        sales = [s for s in sales_data.get('sales', []) if s.get('item_name') == item_name]

        monthly = defaultdict(lambda: {'revenue': 0, 'profit': 0, 'quantity': 0})
        for sale in sales:
            m = sale.get('month', '')
            monthly[m]['revenue'] += sale.get('selling_price', 0) * sale.get('quantity', 0)
            monthly[m]['profit'] += sale.get('profit', 0)
            monthly[m]['quantity'] += sale.get('quantity', 0)

        return jsonify({'success': True, 'data': {
            'product': item_name,
            'monthly_trend': [{'month': k, **v} for k, v in sorted(monthly.items())],
            'total_revenue': round(sum(v['revenue'] for v in monthly.values()), 2),
            'total_profit': round(sum(v['profit'] for v in monthly.values()), 2),
            'total_quantity': sum(v['quantity'] for v in monthly.values())
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# USER MANAGEMENT API (Admin only)
# ============================================================

@app.route('/api/users', methods=['GET'])
@require_admin
def get_users():
    try:
        users_data = load_users()
        # Don't send passwords
        safe_users = [{k: v for k, v in u.items() if k != 'password'} for u in users_data['users']]
        return jsonify({'success': True, 'data': safe_users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@require_admin
def add_user():
    try:
        users_data = load_users()
        new_user = request.get_json()

        if not new_user.get('username') or not new_user.get('password'):
            return jsonify({'success': False, 'message': 'Username and password required'}), 400

        # Check duplicate
        if any(u['username'].lower() == new_user['username'].lower() for u in users_data['users']):
            return jsonify({'success': False, 'message': 'Username already exists'}), 400

        valid_roles = ['admin', 'salesperson']
        if new_user.get('role') not in valid_roles:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400

        users_data['last_id'] += 1
        user = {
            'id': users_data['last_id'],
            'username': new_user['username'].strip(),
            'password': hash_password(new_user['password']),
            'role': new_user['role'],
            'name': new_user.get('name', new_user['username']),
            'email': new_user.get('email', ''),
            'created_at': datetime.now().isoformat(),
            'created_by': session.get('username'),
            'active': True
        }
        users_data['users'].append(user)

        if save_users(users_data):
            log_activity('ADD_USER', f"Created user: {user['username']}", f"Role: {user['role']}")
            safe_user = {k: v for k, v in user.items() if k != 'password'}
            return jsonify({'success': True, 'data': safe_user}), 201
        return jsonify({'success': False, 'message': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    try:
        users_data = load_users()
        update_data = request.get_json()
        user = next((u for u in users_data['users'] if u['id'] == user_id), None)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Prevent modifying own role or the default admin
        if user_id == session.get('user_id') and update_data.get('role') != user['role']:
            return jsonify({'success': False, 'message': 'Cannot change your own role'}), 400

        if 'password' in update_data and update_data['password']:
            user['password'] = hash_password(update_data['password'])

        for field in ['name', 'email', 'role', 'active']:
            if field in update_data:
                user[field] = update_data[field]

        if save_users(users_data):
            log_activity('UPDATE_USER', f"Updated user: {user['username']}")
            safe_user = {k: v for k, v in user.items() if k != 'password'}
            return jsonify({'success': True, 'data': safe_user})
        return jsonify({'success': False, 'message': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    try:
        if user_id == session.get('user_id'):
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
        users_data = load_users()
        user = next((u for u in users_data['users'] if u['id'] == user_id), None)
        if user:
            username = user['username']
            users_data['users'].remove(user)
            if save_users(users_data):
                log_activity('DELETE_USER', f"Deleted user: {username}")
                return jsonify({'success': True, 'message': 'User deleted'})
        return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# ACTIVITY LOGS API (Admin only)
# ============================================================

@app.route('/api/logs', methods=['GET'])
@require_admin
def get_logs():
    try:
        logs_data = load_logs()
        logs = sorted(logs_data.get('logs', []), key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'success': True, 'data': logs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == '__main__':
    init_default_data()
    print("=" * 55)
    print("✓ Sales Analysis System - Upgraded Version")
    print("✓ Login: Admin / Admin123")
    print("✓ Access: http://localhost:5000")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5000, debug=True)
