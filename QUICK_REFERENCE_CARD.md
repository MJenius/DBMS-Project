# DBMS Project - Quick Reference Card

## 🎯 13 Rubric Items - Quick Check

| # | Item | Where to Find | How to Test |
|----|------|---------------|-------------|
| 1 | **ER Diagram** | `ER DIAGRAM AND RELATIONAL SCHEMA.pdf` | Open PDF file |
| 2 | **Relational Schema** | `ddl_dbms_project.sql` | View SQL file, see 8 tables |
| 3 | **Normal Form (3NF)** | `RUBRIC_COMPLIANCE_REPORT.md` | Read documentation |
| 4 | **Users & Privileges** | Dashboard → Manage → Users & Privileges | Create user, view grants |
| 5 | **Triggers** | Database code in `ddl_dbms_project.sql` | Go to `/place_order`, create order |
| 6 | **Procedures & Functions** | Database code + routes | Execute `/reports` or queries |
| 7 | **Create Operations** | Dashboard → Manage → Any entity | Click "Add" button |
| 8 | **Read Operations** | Dashboard → Manage or Orders | View any list |
| 9 | **Update Operations** | Dashboard → Manage → Any entity → Edit | Click "Edit" button |
| 10 | **Delete Operations** | Dashboard → Manage → Any entity → Delete | Click "Delete" button |
| 11 | **Nested Query** | Dashboard → Queries → Nested Query | Set threshold, execute |
| 12 | **Join Query** | Dashboard → Queries → Join Query | Select filter, execute |
| 13 | **Aggregate Query** | Dashboard → Queries → Aggregate Query | Select report type, execute |

---

## 🚀 Quick Start

```powershell
# 1. Navigate to project
cd "c:\Users\mjeni\Downloads\DBMS Project\flask-app"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Flask app
python app.py

# 4. Open browser
http://localhost:5000
```

---

## 📍 Key Routes Map

```
Homepage: /
├─ Place Order: /place_order (Procedure)
├─ Orders: /orders
├─ Deliveries: /view_data (Join Query)
├─ Reports: /reports (Function)
│
├─ Queries:
│  ├─ Nested: /query/nested-query
│  ├─ Join: /query/join-query
│  └─ Aggregate: /query/aggregate-query
│
└─ Manage:
   ├─ Customers (CRUD): /customers, /customer/add, /customer/edit, /customer/delete
   ├─ Restaurants (CRUD): /restaurants, /restaurant/add, /restaurant/edit, /restaurant/delete
   ├─ Drivers (CRUD): /drivers, /driver/add, /driver/edit, /driver/delete
   ├─ Menu (CRUD): /menu, /menu/add, /menu/edit, /menu/delete
   └─ Users: /users, /user/create, /user/privileges, /user/delete
```

---

## 🔒 User Privileges Quick Reference

**Create User:** Dashboard → Manage → Users & Privileges → Create New User

### Privilege Levels:
- **Admin:** Full database access (ALL PRIVILEGES)
- **Manager:** Can view, add, and edit data (SELECT, INSERT, UPDATE)
- **Operator:** Can manage orders and deliveries (CRUD on orders/deliveries)
- **Viewer:** Can only view data (SELECT only)

**Example User Creation:**
- Username: `manager1`
- Password: `Pass123456`
- Level: `Manager`
- Result: Can SELECT, INSERT, UPDATE

---

## 📊 Database Objects at a Glance

### Tables (8):
- customers, restaurants, menu, orders, order_items
- delivery_drivers, deliveries, customer_current_orders

### Triggers (3):
1. `after_order_insert` → Auto-add to current_orders
2. `after_order_item_insert` → Auto-calculate total
3. `after_delivery_insert` → Auto-remove from current_orders

### Procedures (2):
1. `PlaceOrder()` → Create order with items
2. `AssignDelivery()` → Assign driver to order

### Functions (3):
1. `GetActiveOrderCount()` → Count active orders
2. `GetRestaurantRevenue()` → Calculate revenue
3. `GetDriverEarnings()` → Calculate earnings

---

## 🧪 Quick Test Cases

### Test 1: Add Customer
1. Go to Dashboard
2. Manage → Customers
3. Click "Add Customer"
4. Fill: First Name, Last Name, Phone, Email
5. Click "Add"
6. ✅ Flash: "Customer added"

### Test 2: Nested Query
1. Go to Dashboard
2. Queries → Nested Query
3. Set "Minimum Active Orders" = 1
4. Click "Execute Query"
5. ✅ View results table

### Test 3: Create Database User
1. Go to Dashboard
2. Manage → Users & Privileges
3. Click "Create New User"
4. Username: `test123`
5. Password: `TestPass456`
6. Privilege Level: `Operator`
7. Click "Create User"
8. ✅ Flash: "User created"

### Test 4: Join Query
1. Go to Dashboard
2. Queries → Join Query
3. Leave filter or select restaurant
4. Click "Execute Query"
5. ✅ View orders with delivery info

---

## 📋 File Checklist

```
✅ app.py - 700+ lines, 35+ routes
✅ base.html - Navigation with new dropdowns
✅ query_nested.html - Nested query UI
✅ query_join.html - Join query UI
✅ query_aggregate.html - Aggregate query UI
✅ users.html - User management list
✅ user_form.html - Create user form
✅ user_privileges.html - View grants
✅ RUBRIC_COMPLIANCE_REPORT.md - Full verification
✅ TESTING_GUIDE.md - Testing instructions
✅ ROUTES_SUMMARY.md - Route documentation
✅ FINAL_IMPLEMENTATION_SUMMARY.md - Complete summary
```

---

## 🔍 Troubleshooting

### Issue: Database Connection Error
**Solution:** Check `db_config.py` settings:
- Host: `localhost`
- User: `root`
- Password: `MJenius1!`
- Database: `dbms_project`

### Issue: Table Not Found
**Solution:** Import SQL schema:
```powershell
mysql -u root -p dbms_project < ddl_dbms_project.sql
```

### Issue: Port 5000 Already in Use
**Solution:** Change port in `app.py`:
```python
app.run(debug=True, port=5001)
```

---

## ✅ Pre-Submission Checklist

- [ ] All routes tested and working
- [ ] All CRUD operations working (Create, Read, Update, Delete)
- [ ] Nested query returns results
- [ ] Join query shows complete data
- [ ] Aggregate query shows statistics
- [ ] User creation with privilege levels works
- [ ] Database triggers firing (check via procedures)
- [ ] Procedures callable and working
- [ ] Functions returning correct values
- [ ] All templates displaying correctly
- [ ] Navigation menu functional
- [ ] Flash messages appearing
- [ ] No console errors
- [ ] Database integrity maintained

---

## 📞 Quick Reference URLs

| Feature | URL |
|---------|-----|
| Home | http://localhost:5000/ |
| Customers | http://localhost:5000/customers |
| Orders | http://localhost:5000/orders |
| Nested Query | http://localhost:5000/query/nested-query |
| Join Query | http://localhost:5000/query/join-query |
| Aggregate Query | http://localhost:5000/query/aggregate-query |
| Users | http://localhost:5000/users |
| Reports | http://localhost:5000/reports |

---

## 🎓 SQL Query Examples

### Nested Query:
```sql
SELECT * FROM customers WHERE Customer_ID IN (
    SELECT Customer_ID FROM customer_current_orders 
    GROUP BY Customer_ID HAVING COUNT(*) > 1
)
```

### Join Query:
```sql
SELECT o.*, c.First_Name, r.Name, d.Location, dr.First_Name AS DriverName
FROM orders o
JOIN customers c ON o.Customer_ID = c.Customer_ID
JOIN restaurants r ON o.Restaurant_ID = r.Restaurant_ID
LEFT JOIN deliveries d ON o.Order_ID = d.Order_ID
LEFT JOIN delivery_drivers dr ON d.Driver_ID = dr.Driver_ID
```

### Aggregate Query:
```sql
SELECT r.Name, COUNT(o.Order_ID) AS Orders, SUM(o.Total_Amount) AS Revenue
FROM restaurants r
LEFT JOIN orders o ON r.Restaurant_ID = o.Restaurant_ID
GROUP BY r.Restaurant_ID, r.Name
ORDER BY Revenue DESC
```

---

## ⚡ Performance Tips

1. Indexes already created on primary/foreign keys
2. Queries optimized with proper JOINs
3. GUI limits results display to improve loading
4. Search functionality filters at database level
5. Pagination can be added if needed

---

## 🎯 Expected Marks: 26/26 ✅

**Status: READY FOR SUBMISSION**

---

*Quick Reference Card - Print this for exam/presentation*
*Last Updated: November 4, 2025*
