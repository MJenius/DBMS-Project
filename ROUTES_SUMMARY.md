# Flask Routes Summary - DBMS Project

## 🏠 Navigation & Dashboard

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home dashboard with counts |

---

## 🍔 Order Operations

| Route | Method | Description | Procedure/Function |
|-------|--------|-------------|-------------------|
| `/place_order` | GET/POST | Place new order form | `PlaceOrder()` |
| `/orders` | GET | List all orders (searchable) | - |
| `/order/<order_id>` | GET | View order details | - |
| `/assign_delivery` | GET/POST | Assign delivery to driver | `AssignDelivery()` |

---

## 📊 Reports & Queries

| Route | Method | Description | Type | Functions |
|-------|--------|-------------|------|-----------|
| `/reports` | GET | Customer order summary | AGGREGATE | `GetActiveOrderCount()` |
| `/view_data` | GET | Delivery data with joins | JOIN | - |
| `/query/nested-query` | GET/POST | Customers with multiple orders | **NESTED** | - |
| `/query/join-query` | GET/POST | Orders with delivery details | **JOIN** | - |
| `/query/aggregate-query` | GET/POST | Business statistics | **AGGREGATE** | `GetRestaurantRevenue()`, `GetDriverEarnings()` |

---

## 👥 User Management

| Route | Method | Description | Feature |
|-------|--------|-------------|---------|
| `/users` | GET | List all database users | RBAC |
| `/user/create` | GET/POST | Create new user with privileges | RBAC |
| `/user/delete/<username>` | POST | Delete database user | RBAC |
| `/user/privileges/<username>` | GET | View user privileges | RBAC |

---

## 🧑‍💼 CRUD: Customers

| Route | Method | Description |
|-------|--------|-------------|
| `/customers` | GET | List all customers |
| `/customer/add` | GET/POST | Add new customer (CREATE) |
| `/customer/edit/<customer_id>` | GET/POST | Edit customer (UPDATE) |
| `/customer/delete/<customer_id>` | GET | Delete customer (DELETE) |

---

## 🏪 CRUD: Restaurants

| Route | Method | Description |
|-------|--------|-------------|
| `/restaurants` | GET | List all restaurants |
| `/restaurant/add` | GET/POST | Add new restaurant (CREATE) |
| `/restaurant/edit/<restaurant_id>` | GET/POST | Edit restaurant (UPDATE) |
| `/restaurant/delete/<restaurant_id>` | GET | Delete restaurant (DELETE) |

---

## 🚗 CRUD: Drivers

| Route | Method | Description |
|-------|--------|-------------|
| `/drivers` | GET | List all drivers |
| `/driver/add` | GET/POST | Add new driver (CREATE) |
| `/driver/edit/<driver_id>` | GET/POST | Edit driver (UPDATE) |
| `/driver/delete/<driver_id>` | GET | Delete driver (DELETE) |

---

## 🍽️ CRUD: Menu Items

| Route | Method | Description |
|-------|--------|-------------|
| `/menu` | GET | List all menu items |
| `/menu/add` | GET/POST | Add new menu item (CREATE) |
| `/menu/edit/<menu_item_id>` | GET/POST | Edit menu item (UPDATE) |
| `/menu/delete/<menu_item_id>` | GET | Delete menu item (DELETE) |

---

## 📌 Route Statistics

### By Operation Type:
- **CREATE Operations:** 6 routes
- **READ Operations:** 8 routes
- **UPDATE Operations:** 4 routes
- **DELETE Operations:** 5 routes
- **REPORTS/QUERIES:** 5 routes
- **USER MANAGEMENT:** 4 routes
- **DASHBOARD:** 1 route

**Total Routes: 33+**

---

## 🗂️ Navigation Structure

```
Home Dashboard
├── Place Order (Procedure: PlaceOrder)
├── Assign Delivery (Procedure: AssignDelivery)
├── Orders
│   └── Order Details
├── Deliveries (View Data)
├── Reports (Function: GetActiveOrderCount)
│
├── Queries
│   ├── Nested Query (Customers with multiple orders)
│   ├── Join Query (Orders with delivery details)
│   └── Aggregate Query (3 report types)
│       ├── Restaurant Revenue (Function: GetRestaurantRevenue)
│       ├── Driver Earnings (Function: GetDriverEarnings)
│       └── Customer Spending
│
└── Manage
    ├── Customers (CRUD: 4 routes)
    ├── Restaurants (CRUD: 4 routes)
    ├── Drivers (CRUD: 4 routes)
    ├── Menu Items (CRUD: 4 routes)
    └── Users & Privileges (4 routes: View, Create, Delete, View Grants)
```

---

## 🔐 Authentication & Privileges

### Default Admin User:
- **Username:** root
- **Host:** localhost
- **Password:** MJenius1! (in db_config.py)

### Available Privilege Levels:
1. **Admin** - All database operations
2. **Manager** - SELECT, INSERT, UPDATE
3. **Operator** - CRUD on Orders & Deliveries
4. **Viewer** - SELECT only (read-only)

---

## 📱 Request Methods

| Method | Count | Purpose |
|--------|-------|---------|
| GET | 20+ | Display pages, retrieve data, single record operations |
| POST | 13+ | Form submissions, create/update operations |

---

## 🔄 Data Flow Examples

### Place Order Flow:
```
User fills form (/place_order GET)
    ↓
Form submitted (POST /place_order)
    ↓
Calls Procedure: PlaceOrder()
    ↓
Creates orders + order_items
    ↓
Trigger: after_order_insert fires
    ↓
Auto-adds to customer_current_orders
    ↓
Trigger: after_order_item_insert fires
    ↓
Updates Total_Amount
    ↓
Redirect to index with success message
```

### Assign Delivery Flow:
```
User fills form (/assign_delivery GET)
    ↓
Form submitted (POST /assign_delivery)
    ↓
Calls Procedure: AssignDelivery()
    ↓
Creates delivery record
    ↓
Trigger: after_delivery_insert fires
    ↓
Auto-removes from customer_current_orders
    ↓
Redirect to index with success message
```

### Query Execution Flow (Nested Query):
```
User visits /query/nested-query (GET)
    ↓
Form displayed
    ↓
User sets minimum orders = 2
    ↓
Form submitted (POST)
    ↓
Executes nested SQL query
    ↓
Results displayed in table
    ↓
SQL query visible in collapsible section
```

---

## 🎯 Key Features by Route

| Feature | Routes | Count |
|---------|--------|-------|
| **Database Procedures** | /place_order, /assign_delivery | 2 |
| **Database Functions** | /reports, /query/aggregate-query | 2 |
| **Database Triggers** | /place_order, /assign_delivery (indirect) | 2 |
| **RBAC** | /users, /user/create, /user/delete, /user/privileges | 4 |
| **Search/Filter** | /orders, /query/join-query, /query/aggregate-query | 3 |
| **Forms** | /customer/*, /restaurant/*, /driver/*, /menu/*, /user/create | 13 |
| **Tables** | Most read routes | 20+ |

---

## ✅ Rubric Coverage by Routes

### ✅ CRUD Operations
- Customers: `/customers`, `/customer/add`, `/customer/edit/<id>`, `/customer/delete/<id>`
- Restaurants: `/restaurants`, `/restaurant/add`, `/restaurant/edit/<id>`, `/restaurant/delete/<id>`
- Drivers: `/drivers`, `/driver/add`, `/driver/edit/<id>`, `/driver/delete/<id>`
- Menu: `/menu`, `/menu/add`, `/menu/edit/<id>`, `/menu/delete/<id>`

### ✅ User Management & Privileges
- `/users` - View all users with privilege info
- `/user/create` - Create users with 4 privilege levels
- `/user/delete/<username>` - Delete users
- `/user/privileges/<username>` - View grants

### ✅ Procedures & Functions
- **Procedures:** `/place_order`, `/assign_delivery`
- **Functions:** `/reports`, `/query/aggregate-query`

### ✅ Triggers
- Implicit in: `/place_order`, `/assign_delivery`

### ✅ Query Types
- **Nested:** `/query/nested-query`
- **Join:** `/query/join-query`
- **Aggregate:** `/query/aggregate-query`

---

## 📊 Response Formats

| Route Type | Response |
|------------|----------|
| Form GET routes | HTML forms with Bootstrap styling |
| Form POST routes | Redirect + flash message |
| Data GET routes | HTML table with Bootstrap styling |
| Query routes | HTML table + collapsible SQL query |

---

**All routes fully implemented and functional!** ✅
