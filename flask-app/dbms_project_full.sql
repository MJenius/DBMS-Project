-- ============================================================
-- DBMS PROJECT: Online Food Ordering and Delivery Management
-- ============================================================

CREATE DATABASE IF NOT EXISTS dbms_project;
USE dbms_project;

-- ============================================================
-- TABLE CREATION (DDL COMMANDS)
-- ============================================================

CREATE TABLE customers (
    Customer_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Phone_No VARCHAR(15) UNIQUE,
    Email VARCHAR(100)
);

CREATE TABLE restaurants (
    Restaurant_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Address VARCHAR(255),
    Phone_No VARCHAR(15)
);

CREATE TABLE menu (
    Menu_Item_ID INT AUTO_INCREMENT PRIMARY KEY,
    Restaurant_ID INT UNIQUE,
    Name VARCHAR(100),
    Description TEXT,
    Price DECIMAL(10,2),
    FOREIGN KEY (Restaurant_ID) REFERENCES restaurants(Restaurant_ID)
);

CREATE TABLE orders (
    Order_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT,
    Restaurant_ID INT,
    Order_Date DATE,
    Total_Amount DECIMAL(10,2),
    FOREIGN KEY (Customer_ID) REFERENCES customers(Customer_ID),
    FOREIGN KEY (Restaurant_ID) REFERENCES restaurants(Restaurant_ID)
);

CREATE TABLE order_items (
    Order_Item_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_ID INT,
    Menu_Item_ID INT,
    Quantity INT,
    Price DECIMAL(10,2),
    FOREIGN KEY (Order_ID) REFERENCES orders(Order_ID),
    FOREIGN KEY (Menu_Item_ID) REFERENCES menu(Menu_Item_ID)
);

CREATE TABLE delivery_drivers (
    Driver_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Pickup VARCHAR(100),
    Destination VARCHAR(100)
);

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

CREATE TABLE customer_current_orders (
    Customer_ID INT,
    Order_ID INT,
    PRIMARY KEY (Customer_ID, Order_ID),
    FOREIGN KEY (Customer_ID) REFERENCES customers(Customer_ID)
);

-- ============================================================
-- SAMPLE DATA (INSERT COMMANDS)
-- ============================================================

INSERT INTO customers (First_Name, Last_Name, Phone_No, Email)
VALUES 
('Arjun', 'Menon', '9876543210', 'arjun.menon@email.com'),
('Sneha', 'Rao', '9988776655', 'sneha.rao@email.com'),
('Rahul', 'Patel', '9123456789', 'rahul.patel@email.com');

INSERT INTO restaurants (Name, Address, Phone_No)
VALUES 
('Spice Garden', 'MG Road, Bengaluru', '0801234567'),
('Tandoori Nights', 'Koramangala, Bengaluru', '0807654321');

INSERT INTO menu (Restaurant_ID, Name, Description, Price)
VALUES 
(1, 'Paneer Butter Masala', 'Creamy cottage cheese curry', 220.00),
(2, 'Chicken Biryani', 'Hyderabadi style biryani', 250.00);

INSERT INTO delivery_drivers (First_Name, Last_Name, Pickup, Destination)
VALUES 
('Karan', 'Singh', 'Spice Garden', 'Indiranagar'),
('Aisha', 'Khan', 'Tandoori Nights', 'Whitefield'),
('Vikram', 'Das', 'Spice Garden', 'HSR Layout');

INSERT INTO orders (Customer_ID, Restaurant_ID, Order_Date, Total_Amount)
VALUES 
(1, 1, '2025-10-08', 440.00),
(2, 2, '2025-10-07', 250.00),
(3, 1, '2025-10-06', 220.00);

INSERT INTO order_items (Order_ID, Menu_Item_ID, Quantity, Price)
VALUES 
(1, 1, 2, 440.00),
(2, 2, 1, 250.00),
(3, 1, 1, 220.00);

INSERT INTO customer_current_orders (Customer_ID, Order_ID)
VALUES 
(1, 1),
(2, 2),
(3, 3);

-- ============================================================
-- TRIGGERS
-- ============================================================

DELIMITER $$

CREATE TRIGGER after_order_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO Customer_Current_Orders (Customer_ID, Order_ID)
    VALUES (NEW.Customer_ID, NEW.Order_ID);
END $$

CREATE TRIGGER after_order_item_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE Orders
    SET Total_Amount = (
        SELECT COALESCE(SUM(Price), 0)
        FROM Order_Items
        WHERE Order_ID = NEW.Order_ID
    )
    WHERE Order_ID = NEW.Order_ID;
END $$

CREATE TRIGGER after_delivery_insert
AFTER INSERT ON deliveries
FOR EACH ROW
BEGIN
    DELETE FROM Customer_Current_Orders
    WHERE Order_ID = NEW.Order_ID;
END $$

DELIMITER ;

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

DELIMITER $$

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
    FROM Menu
    WHERE Menu_Item_ID = p_menu_item_id;

    INSERT INTO Orders (Customer_ID, Restaurant_ID, Order_Date, Total_Amount)
    VALUES (p_customer_id, p_restaurant_id, p_order_date, 0.00);

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO Order_Items (Order_ID, Menu_Item_ID, Quantity, Price)
    VALUES (v_order_id, p_menu_item_id, p_quantity, v_price * p_quantity);
END $$

CREATE PROCEDURE AssignDelivery(
    IN p_order_id INT,
    IN p_restaurant_id INT,
    IN p_driver_id INT,
    IN p_location VARCHAR(255),
    IN p_fee DECIMAL(10,2)
)
BEGIN
    INSERT INTO Deliveries (Order_ID, Restaurant_ID, Driver_ID, Pickup_Time, Location, Delivery_Fee)
    VALUES (p_order_id, p_restaurant_id, p_driver_id, NOW(), p_location, p_fee);
END $$

DELIMITER ;

-- ============================================================
-- FUNCTIONS
-- ============================================================

DELIMITER $$

CREATE FUNCTION GetActiveOrderCount(p_customer_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt
    FROM Customer_Current_Orders
    WHERE Customer_ID = p_customer_id;
    RETURN cnt;
END $$

CREATE FUNCTION GetRestaurantRevenue(p_restaurant_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT COALESCE(SUM(Total_Amount), 0)
    INTO total
    FROM Orders
    WHERE Restaurant_ID = p_restaurant_id;
    RETURN total;
END $$

CREATE FUNCTION GetDriverEarnings(p_driver_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT COALESCE(SUM(Delivery_Fee), 0)
    INTO total
    FROM Deliveries
    WHERE Driver_ID = p_driver_id;
    RETURN total;
END $$

DELIMITER ;

-- ============================================================
-- NESTED, JOIN, AND AGGREGATE QUERIES
-- ============================================================

-- Nested Query
SELECT Customer_ID, First_Name, Last_Name
FROM customers
WHERE Customer_ID IN (
    SELECT Customer_ID
    FROM orders
    GROUP BY Customer_ID
    HAVING COUNT(Order_ID) > 1
);

-- Join Query
SELECT c.First_Name, c.Last_Name, r.Name AS Restaurant_Name, d.Pickup_Time
FROM deliveries d
JOIN orders o ON d.Order_ID = o.Order_ID
JOIN customers c ON o.Customer_ID = c.Customer_ID
JOIN restaurants r ON o.Restaurant_ID = r.Restaurant_ID;

-- Aggregate Query 1
SELECT r.Name AS Restaurant, SUM(o.Total_Amount) AS Total_Revenue
FROM restaurants r
JOIN orders o ON r.Restaurant_ID = o.Restaurant_ID
GROUP BY r.Restaurant_ID;

-- Aggregate Query 2
SELECT d.Driver_ID, dd.First_Name, dd.Last_Name, COUNT(*) AS Deliveries_Completed
FROM deliveries d
JOIN delivery_drivers dd ON d.Driver_ID = dd.Driver_ID
GROUP BY d.Driver_ID;

-- ============================================================
-- SAMPLE INVOCATION COMMANDS
-- ============================================================

CALL PlaceOrder(1, 1, CURDATE(), 1, 2);
CALL AssignDelivery(1, 1, 2, 'Indiranagar', 40.00);

SELECT GetActiveOrderCount(1);
SELECT GetRestaurantRevenue(1);
SELECT GetDriverEarnings(1);

-- ============================================================
-- END OF FILE
-- ============================================================
