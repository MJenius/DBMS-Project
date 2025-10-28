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
        SELECT c.First_Name, c.Last_Name, r.Name AS Restaurant_Name, d.Pickup_Time, d.Location
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
    cur.execute("DELETE FROM customers WHERE Customer_ID=%s", (customer_id,))
    commit_db()
    flash('Customer deleted', 'warning')
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
    cur.execute("DELETE FROM restaurants WHERE Restaurant_ID=%s", (restaurant_id,))
    commit_db()
    flash('Restaurant deleted', 'warning')
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
    cur.execute("DELETE FROM delivery_drivers WHERE Driver_ID=%s", (driver_id,))
    commit_db()
    flash('Driver deleted', 'warning')
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
    cur.execute("DELETE FROM menu WHERE Menu_Item_ID=%s", (menu_item_id,))
    commit_db()
    flash('Menu item deleted', 'warning')
    return redirect(url_for('menu_items'))

# ----------------------------
if __name__ == '__main__':
    app.run(debug=True)
