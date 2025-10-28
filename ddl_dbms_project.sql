-- ============================================================
-- DATABASE STRUCTURE: Online Food Ordering and Delivery System
-- ============================================================

CREATE DATABASE IF NOT EXISTS dbms_project;
USE dbms_project;

-- ============================================================
-- TABLES
-- ============================================================

-- CUSTOMERS
CREATE TABLE customers (
    Customer_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Phone_No VARCHAR(15) UNIQUE,
    Email VARCHAR(100)
);

-- RESTAURANTS
CREATE TABLE restaurants (
    Restaurant_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Address VARCHAR(255),
    Phone_No VARCHAR(15)
);

-- MENU (1:1 with RESTAURANTS)
CREATE TABLE menu (
    Menu_Item_ID INT AUTO_INCREMENT PRIMARY KEY,
    Restaurant_ID INT UNIQUE,
    Name VARCHAR(100),
    Description TEXT,
    Price DECIMAL(10,2),
    FOREIGN KEY (Restaurant_ID) REFERENCES restaurants(Restaurant_ID)
);

-- ORDERS (Weak entity: depends on Customers and Restaurants)
CREATE TABLE orders (
    Order_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT,
    Restaurant_ID INT,
    Order_Date DATE,
    Total_Amount DECIMAL(10,2),
    FOREIGN KEY (Customer_ID) REFERENCES customers(Customer_ID),
    FOREIGN KEY (Restaurant_ID) REFERENCES restaurants(Restaurant_ID)
);

-- ORDER ITEMS (M:N between ORDERS and MENU)
CREATE TABLE order_items (
    Order_Item_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_ID INT,
    Menu_Item_ID INT,
    Quantity INT,
    Price DECIMAL(10,2),
    FOREIGN KEY (Order_ID) REFERENCES orders(Order_ID),
    FOREIGN KEY (Menu_Item_ID) REFERENCES menu(Menu_Item_ID)
);

-- DELIVERY DRIVERS
CREATE TABLE delivery_drivers (
    Driver_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Pickup VARCHAR(100),
    Destination VARCHAR(100)
);

-- DELIVERIES (Weak entity: depends on Orders, Restaurants, Drivers)
CREATE TABLE deliveries (
    Delivery_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_ID INT,
    Restaurant_ID INT,
    Driver_ID INT,
    Pickup_Time DATETIME,
    Location VARCHAR(255),
    Delivery_Fee DECIMAL(10,2),
    FOREIGN KEY (Order_ID) REFERENCES orders(Order_ID),
    FOREIGN KEY (Restaurant_ID) REFERENCES restaurants(Restaurant_ID),
    FOREIGN KEY (Driver_ID) REFERENCES delivery_drivers(Driver_ID)
);

-- MULTIVALUED ATTRIBUTE: CUSTOMER CURRENT ORDERS
CREATE TABLE customer_current_orders (
    Customer_ID INT,
    Order_ID INT,
    PRIMARY KEY (Customer_ID, Order_ID),
    FOREIGN KEY (Customer_ID) REFERENCES customers(Customer_ID)
);

-- ============================================================
-- TRIGGERS
-- ============================================================

DELIMITER $$

-- Trigger 1: After a new order is placed → Add to current orders
CREATE TRIGGER after_order_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO customer_current_orders (Customer_ID, Order_ID)
    VALUES (NEW.Customer_ID, NEW.Order_ID);
END$$

-- Trigger 2: After adding an order item → Recalculate total
CREATE TRIGGER after_order_item_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET Total_Amount = (
        SELECT COALESCE(SUM(Price), 0)
        FROM order_items
        WHERE Order_ID = NEW.Order_ID
    )
    WHERE Order_ID = NEW.Order_ID;
END$$

-- Trigger 3: After a delivery is completed → Remove from current orders
CREATE TRIGGER after_delivery_insert
AFTER INSERT ON deliveries
FOR EACH ROW
BEGIN
    DELETE FROM customer_current_orders
    WHERE Order_ID = NEW.Order_ID;
END$$

DELIMITER ;

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

DELIMITER $$

-- Procedure: Place a new order
CREATE PROCEDURE PlaceOrder(
    IN p_customer_id INT,
    IN p_restaurant_id INT,
    IN p_order_date DATE,
    IN p_menu_item_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_price DECIMAL(10,2);

    SELECT Price INTO v_price
    FROM menu
    WHERE Menu_Item_ID = p_menu_item_id;

    INSERT INTO orders (Customer_ID, Restaurant_ID, Order_Date, Total_Amount)
    VALUES (p_customer_id, p_restaurant_id, p_order_date, 0.00);

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO order_items (Order_ID, Menu_Item_ID, Quantity, Price)
    VALUES (v_order_id, p_menu_item_id, p_quantity, v_price * p_quantity);
END$$


-- Procedure: Assign a delivery to a driver
CREATE PROCEDURE AssignDelivery(
    IN p_order_id INT,
    IN p_restaurant_id INT,
    IN p_driver_id INT,
    IN p_location VARCHAR(255),
    IN p_fee DECIMAL(10,2)
)
BEGIN
    INSERT INTO deliveries (Order_ID, Restaurant_ID, Driver_ID, Pickup_Time, Location, Delivery_Fee)
    VALUES (p_order_id, p_restaurant_id, p_driver_id, NOW(), p_location, p_fee);
END$$

DELIMITER ;

-- ============================================================
-- FUNCTIONS
-- ============================================================

DELIMITER $$

-- Function 1: Get active order count per customer
CREATE FUNCTION GetActiveOrderCount(p_customer_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt
    FROM customer_current_orders
    WHERE Customer_ID = p_customer_id;
    RETURN cnt;
END$$

-- Function 2: Get total revenue of a restaurant
CREATE FUNCTION GetRestaurantRevenue(p_restaurant_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT COALESCE(SUM(Total_Amount), 0)
    INTO total
    FROM orders
    WHERE Restaurant_ID = p_restaurant_id;
    RETURN total;
END$$

-- Function 3: Get total earnings of a delivery driver
CREATE FUNCTION GetDriverEarnings(p_driver_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT COALESCE(SUM(Delivery_Fee), 0)
    INTO total
    FROM deliveries
    WHERE Driver_ID = p_driver_id;
    RETURN total;
END$$

DELIMITER ;

-- ============================================================
-- END OF DATABASE STRUCTURE
-- ============================================================
