from flask import Flask, render_template, request, redirect, url_for, flash
from db_config import init_mysql
from flask_mysqldb import MySQL
from MySQLdb import OperationalError as MySQLOperationalError
from typing import Any, cast

app = Flask(__name__)
app.secret_key = 'secret123'
mysql: MySQL = init_mysql(app)


def get_cursor():
    """Return a DB cursor; assert mysql is initialized so type-checkers know it's not None."""
    assert mysql is not None
    # Pylance may consider `mysql.connection` optional; cast to Any to narrow type for the checker
    conn = cast(Any, mysql.connection)
    assert conn is not None
    return conn.cursor()


def commit_db():
    """Commit current DB transaction."""
    assert mysql is not None
    conn = cast(Any, mysql.connection)
    assert conn is not None
    conn.commit()

# ----------------------------
# Home Page
# ----------------------------
@app.route('/')
def index():
    cur = get_cursor()
    # gather some quick counts for dashboard
    counts = {}
    try:
        cur.execute('SELECT COUNT(*) AS cnt FROM orders')
        counts['orders'] = cur.fetchone()['cnt']
    except Exception:
        counts['orders'] = 0
    try:
        cur.execute('SELECT COUNT(*) AS cnt FROM deliveries')
        counts['deliveries'] = cur.fetchone()['cnt']
    except Exception:
        counts['deliveries'] = 0
    try:
        cur.execute('SELECT COUNT(*) AS cnt FROM delivery_drivers')
        counts['drivers'] = cur.fetchone()['cnt']
    except Exception:
        counts['drivers'] = 0
    try:
        cur.execute('SELECT COUNT(*) AS cnt FROM restaurants')
        counts['restaurants'] = cur.fetchone()['cnt']
    except Exception:
        counts['restaurants'] = 0

    return render_template('index.html', counts=counts)

# ----------------------------
# Place Order (calls procedure)
# ----------------------------
@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    cur = get_cursor()
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    cur.execute("SELECT * FROM restaurants")
    restaurants = cur.fetchall()
    cur.execute("SELECT * FROM menu")
    menu = cur.fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        restaurant_id = request.form['restaurant_id']
        menu_item_id = request.form['menu_item_id']
        quantity = request.form['quantity']
        cur.callproc('PlaceOrder', (customer_id, restaurant_id, '2025-10-10', menu_item_id, quantity))
        commit_db()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('place_order.html', customers=customers, restaurants=restaurants, menu=menu)

# ----------------------------
# Assign Delivery (procedure)
# ----------------------------
@app.route('/assign_delivery', methods=['GET', 'POST'])
def assign_delivery():
    cur = get_cursor()
    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()
    cur.execute("SELECT * FROM delivery_drivers")
    drivers = cur.fetchall()
    cur.execute("SELECT * FROM restaurants")
    restaurants = cur.fetchall()

    if request.method == 'POST':
        order_id = request.form['order_id']
        restaurant_id = request.form['restaurant_id']
        driver_id = request.form['driver_id']
        location = request.form['location']
        fee = request.form['fee']
        cur.callproc('AssignDelivery', (order_id, restaurant_id, driver_id, location, fee))
        commit_db()
        flash('Delivery assigned successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('assign_delivery.html', orders=orders, drivers=drivers, restaurants=restaurants)

# ----------------------------
# View Data and Reports
# ----------------------------
@app.route('/view_data')
def view_data():
    cur = get_cursor()
    cur.execute("""
        SELECT d.Delivery_ID as delivery_id, c.First_Name, c.Last_Name, r.Name AS Restaurant_Name, d.Pickup_Time, d.Location
        FROM deliveries d
        JOIN orders o ON d.Order_ID = o.Order_ID
        JOIN customers c ON o.Customer_ID = c.Customer_ID
        JOIN restaurants r ON o.Restaurant_ID = r.Restaurant_ID
    """)
    records = cur.fetchall()
    return render_template('view_data.html', records=records)


# ----------------------------
# Orders list and details (read-only)
# ----------------------------
@app.route('/orders')
def orders():
    q = request.args.get('q', '').strip()
    cur = get_cursor()
    base_sql = """
        SELECT o.Order_ID, o.Order_Date, c.First_Name, c.Last_Name, r.Name AS Restaurant
        FROM orders o
        JOIN customers c ON o.Customer_ID = c.Customer_ID
        JOIN restaurants r ON o.Restaurant_ID = r.Restaurant_ID
        ORDER BY o.Order_ID DESC
    """
    if q:
        # simple search: by order id or customer name
        if q.isdigit():
            cur.execute("SELECT o.Order_ID, o.Order_Date, c.First_Name, c.Last_Name, r.Name AS Restaurant FROM orders o JOIN customers c ON o.Customer_ID=c.Customer_ID JOIN restaurants r ON o.Restaurant_ID=r.Restaurant_ID WHERE o.Order_ID=%s", (q,))
        else:
            cur.execute("SELECT o.Order_ID, o.Order_Date, c.First_Name, c.Last_Name, r.Name AS Restaurant FROM orders o JOIN customers c ON o.Customer_ID=c.Customer_ID JOIN restaurants r ON o.Restaurant_ID=r.Restaurant_ID WHERE CONCAT(c.First_Name,' ',c.Last_Name) LIKE %s", (f"%{q}%",))
    else:
        cur.execute(base_sql)

    rows = cur.fetchall()
    return render_template('orders.html', orders=rows, q=q)


@app.route('/order/<int:order_id>')
def order_detail(order_id: int):
    cur = get_cursor()
    # Some schemas may not include a Phone column on customers; try the richer query first
    try:
        cur.execute(
            "SELECT o.*, c.First_Name, c.Last_Name, c.Phone, r.Name AS Restaurant "
            "FROM orders o JOIN customers c ON o.Customer_ID=c.Customer_ID "
            "JOIN restaurants r ON o.Restaurant_ID=r.Restaurant_ID WHERE o.Order_ID=%s",
            (order_id,)
        )
    except MySQLOperationalError:
        # Fallback to a query that doesn't reference c.Phone
        cur.execute(
            "SELECT o.*, c.First_Name, c.Last_Name, r.Name AS Restaurant "
            "FROM orders o JOIN customers c ON o.Customer_ID=c.Customer_ID "
            "JOIN restaurants r ON o.Restaurant_ID=r.Restaurant_ID WHERE o.ORDER_ID=%s",
            (order_id,)
        )
    order = cur.fetchone()

    # try to fetch order items if table exists
    items = []
    try:
        cur.execute("SELECT oi.*, m.Name AS MenuName, m.Price FROM order_items oi JOIN menu m ON oi.Menu_Item_ID = m.Menu_Item_ID WHERE oi.Order_ID=%s", (order_id,))
        items = cur.fetchall()
    except Exception:
        items = []

    # deliveries for this order
    deliveries = []
    try:
        cur.execute("SELECT * FROM deliveries WHERE Order_ID=%s", (order_id,))
        deliveries = cur.fetchall()
    except Exception:
        deliveries = []

    return render_template('order_detail.html', order=order, items=items, deliveries=deliveries)


@app.route('/order/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id: int):
    """
    Delete an order and all related data (order items and deliveries)
    """
    cur = get_cursor()
    try:
        # Get order info for the message
        cur.execute("SELECT o.Order_ID, CONCAT(c.First_Name, ' ', c.Last_Name) as customer_name FROM orders o JOIN customers c ON o.Customer_ID=c.Customer_ID WHERE o.Order_ID=%s", (order_id,))
        order = cur.fetchone()
        order_info = f"Order #{order_id} from {order['customer_name']}" if order else f"Order #{order_id}"
        
        # Delete in correct order to respect foreign keys
        # 1. Delete deliveries for this order
        cur.execute("DELETE FROM deliveries WHERE Order_ID=%s", (order_id,))
        
        # 2. Delete order items
        cur.execute("DELETE FROM order_items WHERE Order_ID=%s", (order_id,))
        
        # 3. Delete the order itself
        cur.execute("DELETE FROM orders WHERE Order_ID=%s", (order_id,))
        
        commit_db()
        flash(f'{order_info} and all associated data has been deleted successfully', 'success')
    except Exception as e:
        # Rollback on error
        assert mysql is not None
        conn = cast(Any, mysql.connection)
        assert conn is not None
        conn.rollback()
        
        flash(f'Error deleting order: {str(e)}', 'danger')
    
    return redirect(url_for('orders'))


@app.route('/delivery/delete/<int:delivery_id>', methods=['POST'])
def delete_delivery(delivery_id: int):
    """
    Delete a delivery record
    """
    cur = get_cursor()
    try:
        # Get delivery info for the message
        cur.execute("SELECT Location FROM deliveries WHERE Delivery_ID=%s", (delivery_id,))
        delivery = cur.fetchone()
        delivery_info = f"Delivery #{delivery_id} to {delivery['Location']}" if delivery else f"Delivery #{delivery_id}"
        
        # Delete the delivery
        cur.execute("DELETE FROM deliveries WHERE Delivery_ID=%s", (delivery_id,))
        commit_db()
        flash(f'{delivery_info} has been deleted successfully', 'success')
    except Exception as e:
        # Rollback on error
        assert mysql is not None
        conn = cast(Any, mysql.connection)
        assert conn is not None
        conn.rollback()
        
        flash(f'Error deleting delivery: {str(e)}', 'danger')
    
    return redirect(url_for('view_data'))

# ----------------------------
# Function Calls (reports)
# ----------------------------
@app.route('/reports')
def reports():
    cur = get_cursor()
    cur.execute("SELECT Customer_ID, CONCAT(First_Name, ' ', Last_Name) AS Name FROM customers")
    customers = cur.fetchall()

    customer_data = []
    for c in customers:
        cur.execute(f"SELECT GetActiveOrderCount({c['Customer_ID']}) AS ActiveOrders")
        active = cur.fetchone()['ActiveOrders']
        customer_data.append({'name': c['Name'], 'active_orders': active})

    return render_template('reports.html', customer_data=customer_data)


# ----------------------------
# Query 1: NESTED QUERY - Customers with multiple orders
# ----------------------------
@app.route('/query/nested-query', methods=['GET', 'POST'])
def nested_query():
    """
    Nested Query: Find customers with more than X active orders
    """
    cur = get_cursor()
    results = []
    min_orders = 0
    
    if request.method == 'POST':
        min_orders = int(request.form.get('min_orders', 1))
        
        # NESTED QUERY: Select customers who have active orders > min_orders
        query = """
        SELECT Customer_ID, CONCAT(First_Name, ' ', Last_Name) AS CustomerName, Email, Phone_No
        FROM customers
        WHERE Customer_ID IN (
            SELECT Customer_ID FROM customer_current_orders
            GROUP BY Customer_ID
            HAVING COUNT(*) > %s
        )
        ORDER BY Customer_ID
        """
        cur.execute(query, (min_orders,))
        results = cur.fetchall()
        
        if not results:
            flash(f'No customers found with more than {min_orders} active orders.', 'info')
    
    return render_template('query_nested.html', results=results, min_orders=min_orders)


# ----------------------------
# Query 2: JOIN QUERY - Orders with delivery details
# ----------------------------
@app.route('/query/join-query', methods=['GET', 'POST'])
def join_query():
    """
    Join Query: Find orders with their delivery and restaurant information
    """
    cur = get_cursor()
    results = []
    restaurant_filter = ''
    
    if request.method == 'POST':
        restaurant_filter = request.form.get('restaurant_id', '')
        
        # JOIN QUERY: Select orders with complete delivery and restaurant information
        if restaurant_filter and restaurant_filter.isdigit():
            query = """
            SELECT 
                o.Order_ID,
                CONCAT(c.First_Name, ' ', c.Last_Name) AS CustomerName,
                r.Name AS RestaurantName,
                o.Order_Date,
                o.Total_Amount,
                d.Delivery_ID,
                d.Location,
                d.Delivery_Fee,
                CONCAT(dr.First_Name, ' ', dr.Last_Name) AS DriverName
            FROM orders o
            JOIN customers c ON o.Customer_ID = c.Customer_ID
            JOIN restaurants r ON o.Restaurant_ID = r.Restaurant_ID
            LEFT JOIN deliveries d ON o.Order_ID = d.Order_ID
            LEFT JOIN delivery_drivers dr ON d.Driver_ID = dr.Driver_ID
            WHERE r.Restaurant_ID = %s
            ORDER BY o.Order_Date DESC
            """
            cur.execute(query, (restaurant_filter,))
        else:
            query = """
            SELECT 
                o.Order_ID,
                CONCAT(c.First_Name, ' ', c.Last_Name) AS CustomerName,
                r.Name AS RestaurantName,
                o.Order_Date,
                o.Total_Amount,
                d.Delivery_ID,
                d.Location,
                d.Delivery_Fee,
                CONCAT(dr.First_Name, ' ', dr.Last_Name) AS DriverName
            FROM orders o
            JOIN customers c ON o.Customer_ID = c.Customer_ID
            JOIN restaurants r ON o.Restaurant_ID = r.Restaurant_ID
            LEFT JOIN deliveries d ON o.Order_ID = d.Order_ID
            LEFT JOIN delivery_drivers dr ON d.Driver_ID = dr.Driver_ID
            ORDER BY o.Order_Date DESC
            LIMIT 50
            """
            cur.execute(query)
        
        results = cur.fetchall()
        
        if not results:
            flash('No orders found matching the criteria.', 'info')
    
    # Get restaurants for filter dropdown
    cur.execute("SELECT Restaurant_ID, Name FROM restaurants ORDER BY Name")
    restaurants = cur.fetchall()
    
    return render_template('query_join.html', results=results, restaurants=restaurants, selected_restaurant=restaurant_filter)


# ----------------------------
# Query 3: AGGREGATE QUERY - Revenue and statistics
# ----------------------------
@app.route('/query/aggregate-query', methods=['GET', 'POST'])
def aggregate_query():
    """
    Aggregate Query: Calculate revenue, order counts, and statistics
    """
    cur = get_cursor()
    results = []
    query_type = 'all_restaurants'
    
    if request.method == 'POST':
        query_type = request.form.get('query_type', 'all_restaurants')
        
        if query_type == 'all_restaurants':
            # AGGREGATE QUERY: Restaurant revenue and order statistics
            query = """
            SELECT 
                r.Restaurant_ID,
                r.Name,
                COUNT(DISTINCT o.Order_ID) AS TotalOrders,
                COALESCE(SUM(o.Total_Amount), 0) AS TotalRevenue,
                ROUND(AVG(o.Total_Amount), 2) AS AvgOrderValue,
                MAX(o.Total_Amount) AS HighestOrder,
                MIN(o.Total_Amount) AS LowestOrder
            FROM restaurants r
            LEFT JOIN orders o ON r.Restaurant_ID = o.Restaurant_ID
            GROUP BY r.Restaurant_ID, r.Name
            HAVING COUNT(DISTINCT o.Order_ID) > 0
            ORDER BY TotalRevenue DESC
            """
            cur.execute(query)
            results = cur.fetchall()
            
            if not results:
                flash('No restaurants with orders found.', 'info')
        
        elif query_type == 'driver_earnings':
            # AGGREGATE QUERY: Driver earnings statistics
            query = """
            SELECT 
                dr.Driver_ID,
                CONCAT(dr.First_Name, ' ', dr.Last_Name) AS DriverName,
                COUNT(DISTINCT d.Delivery_ID) AS TotalDeliveries,
                COALESCE(SUM(d.Delivery_Fee), 0) AS TotalEarnings,
                ROUND(AVG(d.Delivery_Fee), 2) AS AvgFeePerDelivery
            FROM delivery_drivers dr
            LEFT JOIN deliveries d ON dr.Driver_ID = d.Driver_ID
            GROUP BY dr.Driver_ID, dr.First_Name, dr.Last_Name
            ORDER BY TotalEarnings DESC
            """
            cur.execute(query)
            results = cur.fetchall()
            
            if not results:
                flash('No driver earnings data found.', 'info')
        
        elif query_type == 'customer_spending':
            # AGGREGATE QUERY: Customer spending statistics
            query = """
            SELECT 
                c.Customer_ID,
                CONCAT(c.First_Name, ' ', c.Last_Name) AS CustomerName,
                COUNT(DISTINCT o.Order_ID) AS TotalOrders,
                COALESCE(SUM(o.Total_Amount), 0) AS TotalSpent,
                ROUND(AVG(o.Total_Amount), 2) AS AvgOrderValue
            FROM customers c
            LEFT JOIN orders o ON c.Customer_ID = o.Customer_ID
            GROUP BY c.Customer_ID, c.First_Name, c.Last_Name
            HAVING COUNT(DISTINCT o.Order_ID) > 0
            ORDER BY TotalSpent DESC
            """
            cur.execute(query)
            results = cur.fetchall()
            
            if not results:
                flash('No customer spending data found.', 'info')
    
    return render_template('query_aggregate.html', results=results, query_type=query_type)


# ----------------------------
# CRUD: Customers
# ----------------------------
@app.route('/customers')
def customers():
    cur = get_cursor()
    cur.execute("SELECT * FROM customers ORDER BY Customer_ID DESC")
    rows = cur.fetchall()
    return render_template('customers.html', customers=rows)


@app.route('/customer/add', methods=['GET', 'POST'])
def add_customer():
    cur = get_cursor()
    if request.method == 'POST':
        fn = request.form['first_name']
        ln = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']
        cur.execute("INSERT INTO customers (First_Name, Last_Name, Phone_No, Email) VALUES (%s,%s,%s,%s)", (fn, ln, phone, email))
        commit_db()
        flash('Customer added', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None)


@app.route('/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id: int):
    cur = get_cursor()
    if request.method == 'POST':
        fn = request.form['first_name']
        ln = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']
        cur.execute("UPDATE customers SET First_Name=%s, Last_Name=%s, Phone_No=%s, Email=%s WHERE Customer_ID=%s", (fn, ln, phone, email, customer_id))
        commit_db()
        flash('Customer updated', 'success')
        return redirect(url_for('customers'))
    cur.execute("SELECT * FROM customers WHERE Customer_ID=%s", (customer_id,))
    customer = cur.fetchone()
    return render_template('customer_form.html', customer=customer)


@app.route('/customer/delete/<int:customer_id>')
def delete_customer(customer_id: int):
    cur = get_cursor()
    try:
        # First, get customer name for the message
        cur.execute("SELECT CONCAT(First_Name, ' ', Last_Name) as name FROM customers WHERE Customer_ID=%s", (customer_id,))
        customer = cur.fetchone()
        customer_name = customer['name'] if customer else 'Customer'
        
        # Get all order IDs for this customer
        cur.execute("SELECT Order_ID FROM orders WHERE Customer_ID=%s", (customer_id,))
        orders = cur.fetchall()
        
        # Delete all related data in correct order
        for order in orders:
            order_id = order['Order_ID']
            # Delete deliveries for this order
            cur.execute("DELETE FROM deliveries WHERE Order_ID=%s", (order_id,))
            # Delete order items
            cur.execute("DELETE FROM order_items WHERE Order_ID=%s", (order_id,))
            # Delete the order
            cur.execute("DELETE FROM orders WHERE Order_ID=%s", (order_id,))
        
        # Delete from customer_current_orders (NEW LINE)
        cur.execute("DELETE FROM customer_current_orders WHERE Customer_ID=%s", (customer_id,))
        
        # Finally delete the customer
        cur.execute("DELETE FROM customers WHERE Customer_ID=%s", (customer_id,))
        commit_db()
        
        order_count = len(orders) if orders else 0
        if order_count > 0:
            flash(f'Customer "{customer_name}" and their {order_count} order(s) with all associated data have been deleted successfully', 'success')
        else:
            flash(f'Customer "{customer_name}" has been deleted successfully', 'success')
    except Exception as e:
        # Rollback on error
        assert mysql is not None
        conn = cast(Any, mysql.connection)
        assert conn is not None
        conn.rollback()
        
        # Handle foreign key constraint errors gracefully
        if 'foreign key' in str(e).lower():
            flash(f'Error deleting customer data. There may be external references to this customer.', 'danger')
        elif 'constraint' in str(e).lower():
            flash(f'Cannot delete this customer due to data constraints. Please contact support.', 'danger')
        else:
            flash(f'Error deleting customer: {str(e)}', 'danger')
    
    return redirect(url_for('customers'))

# ----------------------------
# CRUD: Restaurants
# ----------------------------
@app.route('/restaurants')
def restaurants():
    cur = get_cursor()
    cur.execute("SELECT * FROM restaurants ORDER BY Restaurant_ID DESC")
    rows = cur.fetchall()
    return render_template('restaurants.html', restaurants=rows)


@app.route('/restaurant/add', methods=['GET', 'POST'])
def add_restaurant():
    cur = get_cursor()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        cur.execute("INSERT INTO restaurants (Name, Address, Phone_No) VALUES (%s,%s,%s)", (name, address, phone))
        commit_db()
        flash('Restaurant added', 'success')
        return redirect(url_for('restaurants'))
    return render_template('restaurant_form.html', restaurant=None)


@app.route('/restaurant/edit/<int:restaurant_id>', methods=['GET', 'POST'])
def edit_restaurant(restaurant_id: int):
    cur = get_cursor()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        cur.execute("UPDATE restaurants SET Name=%s, Address=%s, Phone_No=%s WHERE Restaurant_ID=%s", (name, address, phone, restaurant_id))
        commit_db()
        flash('Restaurant updated', 'success')
        return redirect(url_for('restaurants'))
    cur.execute("SELECT * FROM restaurants WHERE Restaurant_ID=%s", (restaurant_id,))
    restaurant = cur.fetchone()
    return render_template('restaurant_form.html', restaurant=restaurant)


@app.route('/restaurant/delete/<int:restaurant_id>')
def delete_restaurant(restaurant_id: int):
    cur = get_cursor()
    try:
        # Get restaurant name for the message
        cur.execute("SELECT Name FROM restaurants WHERE Restaurant_ID=%s", (restaurant_id,))
        restaurant = cur.fetchone()
        restaurant_name = restaurant['Name'] if restaurant else 'Restaurant'
        
        # Try to delete the restaurant
        cur.execute("DELETE FROM restaurants WHERE Restaurant_ID=%s", (restaurant_id,))
        commit_db()
        flash(f'Restaurant "{restaurant_name}" has been deleted successfully', 'success')
    except Exception as e:
        # Rollback on error
        assert mysql is not None
        conn = cast(Any, mysql.connection)
        assert conn is not None
        conn.rollback()
        
        # Handle foreign key constraint errors gracefully
        if 'foreign key' in str(e).lower():
            flash(f'Cannot delete this restaurant because it has menu items, orders, or deliveries associated with it. Please handle related data first.', 'danger')
        elif 'constraint' in str(e).lower():
            flash(f'Cannot delete this restaurant due to related data constraints. Please ensure all associated records are removed first.', 'danger')
        else:
            flash(f'Error deleting restaurant: {str(e)}', 'danger')
    
    return redirect(url_for('restaurants'))


# ----------------------------
# CRUD: Drivers
# ----------------------------
@app.route('/drivers')
def drivers():
    cur = get_cursor()
    cur.execute("SELECT * FROM delivery_drivers ORDER BY Driver_ID DESC")
    rows = cur.fetchall()
    return render_template('drivers.html', drivers=rows)


@app.route('/driver/add', methods=['GET', 'POST'])
def add_driver():
    cur = get_cursor()
    if request.method == 'POST':
        fn = request.form['first_name']
        ln = request.form['last_name']
        pickup = request.form['pickup']
        dest = request.form['destination']
        cur.execute("INSERT INTO delivery_drivers (First_Name, Last_Name, Pickup, Destination) VALUES (%s,%s,%s,%s)", (fn, ln, pickup, dest))
        commit_db()
        flash('Driver added', 'success')
        return redirect(url_for('drivers'))
    return render_template('driver_form.html', driver=None)


@app.route('/driver/edit/<int:driver_id>', methods=['GET', 'POST'])
def edit_driver(driver_id: int):
    cur = get_cursor()
    if request.method == 'POST':
        fn = request.form['first_name']
        ln = request.form['last_name']
        pickup = request.form['pickup']
        dest = request.form['destination']
        cur.execute("UPDATE delivery_drivers SET First_Name=%s, Last_Name=%s, Pickup=%s, Destination=%s WHERE Driver_ID=%s", (fn, ln, pickup, dest, driver_id))
        commit_db()
        flash('Driver updated', 'success')
        return redirect(url_for('drivers'))
    cur.execute("SELECT * FROM delivery_drivers WHERE Driver_ID=%s", (driver_id,))
    driver = cur.fetchone()
    return render_template('driver_form.html', driver=driver)


@app.route('/driver/delete/<int:driver_id>')
def delete_driver(driver_id: int):
    cur = get_cursor()
    try:
        # Get driver name for the message
        cur.execute("SELECT CONCAT(First_Name, ' ', Last_Name) as name FROM delivery_drivers WHERE Driver_ID=%s", (driver_id,))
        driver = cur.fetchone()
        driver_name = driver['name'] if driver else 'Driver'
        
        # Try to delete the driver
        cur.execute("DELETE FROM delivery_drivers WHERE Driver_ID=%s", (driver_id,))
        commit_db()
        flash(f'Driver "{driver_name}" has been deleted successfully', 'success')
    except Exception as e:
        # Rollback on error
        assert mysql is not None
        conn = cast(Any, mysql.connection)
        assert conn is not None
        conn.rollback()
        
        # Handle foreign key constraint errors gracefully
        if 'foreign key' in str(e).lower():
            flash(f'Cannot delete this driver because they have active deliveries assigned. Please reassign or complete their deliveries first.', 'danger')
        elif 'constraint' in str(e).lower():
            flash(f'Cannot delete this driver due to related delivery records. Please ensure all associated deliveries are handled first.', 'danger')
        else:
            flash(f'Error deleting driver: {str(e)}', 'danger')
    
    return redirect(url_for('drivers'))


# ----------------------------
# CRUD: Menu Items
# ----------------------------
@app.route('/menu')
def menu_items():
    cur = get_cursor()
    cur.execute("SELECT * FROM menu ORDER BY Menu_Item_ID DESC")
    rows = cur.fetchall()
    return render_template('menu_items.html', menu=rows)


@app.route('/menu/add', methods=['GET', 'POST'])
def add_menu_item():
    cur = get_cursor()
    cur.execute("SELECT * FROM restaurants ORDER BY Name")
    restaurants = cur.fetchall()
    if request.method == 'POST':
        name = request.form['name']
        restaurant_id = request.form['restaurant_id']
        description = request.form.get('description','')
        price = request.form['price']
        cur.execute("INSERT INTO menu (Restaurant_ID, Name, Description, Price) VALUES (%s,%s,%s,%s)", (restaurant_id, name, description, price))
        commit_db()
        flash('Menu item added', 'success')
        return redirect(url_for('menu_items'))
    return render_template('menu_form.html', item=None, restaurants=restaurants)


@app.route('/menu/edit/<int:menu_item_id>', methods=['GET', 'POST'])
def edit_menu_item(menu_item_id: int):
    cur = get_cursor()
    cur.execute("SELECT * FROM restaurants ORDER BY Name")
    restaurants = cur.fetchall()
    if request.method == 'POST':
        name = request.form['name']
        restaurant_id = request.form['restaurant_id']
        description = request.form.get('description','')
        price = request.form['price']
        cur.execute("UPDATE menu SET Name=%s, Restaurant_ID=%s, Description=%s, Price=%s WHERE Menu_Item_ID=%s", (name, restaurant_id, description, price, menu_item_id))
        commit_db()
        flash('Menu item updated', 'success')
        return redirect(url_for('menu_items'))
    cur.execute("SELECT * FROM menu WHERE Menu_Item_ID=%s", (menu_item_id,))
    item = cur.fetchone()
    return render_template('menu_form.html', item=item, restaurants=restaurants)


@app.route('/menu/delete/<int:menu_item_id>')
def delete_menu_item(menu_item_id: int):
    cur = get_cursor()
    try:
        cur.execute("DELETE FROM menu WHERE Menu_Item_ID=%s", (menu_item_id,))
        commit_db()
        flash('Menu item deleted', 'warning')
    except Exception as e:
        # Rollback the transaction on error
        assert mysql is not None
        conn = cast(Any, mysql.connection)
        assert conn is not None
        conn.rollback()
        
        # Check if foreign key constraint error
        if 'foreign key' in str(e).lower():
            flash(f'Cannot delete this menu item because it is referenced in active orders. Please check order history or contact support.', 'danger')
        else:
            flash(f'Error deleting menu item: {str(e)}', 'danger')
    
    return redirect(url_for('menu_items'))


# ----------------------------
# USER MANAGEMENT: Create Users and Grant Privileges
# ----------------------------
@app.route('/users')
def users():
    """
    Display list of database users and their privileges
    """
    cur = get_cursor()
    try:
        cur.execute("SELECT user, host FROM mysql.user ORDER BY user")
        users_list = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching users: {str(e)}', 'danger')
        users_list = []
    
    return render_template('users.html', users=users_list)


@app.route('/user/create', methods=['GET', 'POST'])
def create_user():
    """
    Create a new database user with specific privileges
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        privilege_level = request.form['privilege_level']
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('user_form.html')
        
        cur = get_cursor()
        try:
            # Create user
            cur.execute(f"CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{password}'")
            
            # Grant privileges based on role
            if privilege_level == 'admin':
                cur.execute(f"GRANT ALL PRIVILEGES ON dbms_project.* TO '{username}'@'localhost'")
                privilege_desc = "All Privileges (Admin)"
            elif privilege_level == 'manager':
                cur.execute(f"GRANT SELECT, INSERT, UPDATE ON dbms_project.* TO '{username}'@'localhost'")
                privilege_desc = "Select, Insert, Update (Manager)"
            elif privilege_level == 'viewer':
                cur.execute(f"GRANT SELECT ON dbms_project.* TO '{username}'@'localhost'")
                privilege_desc = "Select Only (Viewer)"
            elif privilege_level == 'operator':
                # Operator can do CRUD on specific tables
                cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON dbms_project.orders TO '{username}'@'localhost'")
                cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON dbms_project.order_items TO '{username}'@'localhost'")
                cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON dbms_project.deliveries TO '{username}'@'localhost'")
                privilege_desc = "Order/Delivery Operations (Operator)"
            
            cur.execute("FLUSH PRIVILEGES")
            commit_db()
            
            flash(f'User "{username}" created with {privilege_desc}', 'success')
            return redirect(url_for('users'))
        
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'danger')
            return render_template('user_form.html')
    
    return render_template('user_form.html')


@app.route('/user/delete/<username>', methods=['POST'])
def delete_user(username: str):
    """
    Delete a database user
    """
    # Protect system users from deletion
    protected_users = ['root', 'admin', 'mysql.sys', 'mysql.session', 'mysql.infoschema']
    if username.lower() in protected_users:
        flash(f'Cannot delete system user: {username}. This user is protected.', 'danger')
        return redirect(url_for('users'))
    
    cur = get_cursor()
    try:
        cur.execute(f"DROP USER IF EXISTS '{username}'@'localhost'")
        cur.execute("FLUSH PRIVILEGES")
        commit_db()
        flash(f'User "{username}" deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('users'))


@app.route('/user/privileges/<username>')
def user_privileges(username: str):
    """
    View and manage privileges for a specific user
    """
    cur = get_cursor()
    try:
        # Get user grants information
        cur.execute(f"SHOW GRANTS FOR '{username}'@'localhost'")
        grants = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching privileges: {str(e)}', 'danger')
        grants = []
    
    return render_template('user_privileges.html', username=username, grants=grants)


@app.route('/user/privileges/<username>/update', methods=['POST'])
def update_user_privileges(username: str):
    """
    Update privileges for a specific user
    """
    # Protect system users
    protected_users = ['root', 'admin', 'mysql.sys', 'mysql.session', 'mysql.infoschema']
    if username.lower() in protected_users:
        flash(f'Cannot modify privileges for system user: {username}', 'danger')
        return redirect(url_for('user_privileges', username=username))
    
    cur = get_cursor()
    try:
        privilege_level = request.form.get('privilege_level', 'viewer')
        
        # First, revoke all current privileges
        cur.execute(f"REVOKE ALL PRIVILEGES ON dbms_project.* FROM '{username}'@'localhost'")
        
        # Grant new privileges based on role
        if privilege_level == 'admin':
            cur.execute(f"GRANT ALL PRIVILEGES ON dbms_project.* TO '{username}'@'localhost'")
        elif privilege_level == 'manager':
            cur.execute(f"GRANT SELECT, INSERT, UPDATE ON dbms_project.* TO '{username}'@'localhost'")
        elif privilege_level == 'operator':
            cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON dbms_project.* TO '{username}'@'localhost'")
        else:  # viewer
            cur.execute(f"GRANT SELECT ON dbms_project.* TO '{username}'@'localhost'")
        
        cur.execute("FLUSH PRIVILEGES")
        commit_db()
        flash(f'Privileges updated for user "{username}" to {privilege_level.upper()}', 'success')
    except Exception as e:
        flash(f'Error updating privileges: {str(e)}', 'danger')
    
    return redirect(url_for('user_privileges', username=username))


# ----------------------------
if __name__ == '__main__':
    app.run(debug=True)
