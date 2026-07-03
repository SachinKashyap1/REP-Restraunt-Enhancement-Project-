-- ============================================================
-- RESTAURANT MANAGEMENT SYSTEM - MySQL Workbench Schema
-- ============================================================

-- Create and use the database
DROP DATABASE IF EXISTS restaurant_management_system;
CREATE DATABASE restaurant_management_system;
USE restaurant_management_system;

-- ============================================================
-- 1. CUSTOMER TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS CUSTOMER (
    Customer_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name        VARCHAR(100) NOT NULL,
    Phone_No    VARCHAR(15)  NOT NULL,
    Email       VARCHAR(100) UNIQUE,
    Address     TEXT,
    Created_At  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. STAFF TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS STAFF (
    Staff_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Name       VARCHAR(100) NOT NULL,
    Role       ENUM('Waiter','Chef','Manager','Cashier','Host') NOT NULL,
    Phone_No   VARCHAR(15),
    Salary     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    Joined_At  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. TABLE_INFO TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS TABLE_INFO (
    Table_ID  INT AUTO_INCREMENT PRIMARY KEY,
    Capacity  INT NOT NULL DEFAULT 4,
    Location  ENUM('Indoor','Outdoor','Rooftop','Private Room') NOT NULL DEFAULT 'Indoor',
    Status    ENUM('Available','Occupied','Reserved') DEFAULT 'Available'
);

-- ============================================================
-- 4. MENU_ITEM TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS MENU_ITEM (
    Item_ID       INT AUTO_INCREMENT PRIMARY KEY,
    Item_Name     VARCHAR(100) NOT NULL,
    Price         DECIMAL(10,2) NOT NULL,
    Category      ENUM('Starter','Main Course','Dessert','Beverage','Snack','Combo') NOT NULL,
    Description   TEXT,
    Rating        DECIMAL(3,2) DEFAULT 0.00,
    Times_Ordered INT DEFAULT 0,
    Is_Available  BOOLEAN DEFAULT 1,
    Image_URL     VARCHAR(255),
    Created_At    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. ORDERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ORDERS (
    Order_ID     INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID  INT NOT NULL,
    Staff_ID     INT NOT NULL,
    Table_ID     INT NOT NULL,
    Total_Price  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    Payment_Mode ENUM('Cash','Card','UPI','Online') NOT NULL DEFAULT 'Cash',
    Order_Status ENUM('Pending','Preparing','Served','Completed','Cancelled') DEFAULT 'Pending',
    Order_Date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    Notes        TEXT,
    FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID) ON DELETE RESTRICT,
    FOREIGN KEY (Staff_ID)    REFERENCES STAFF(Staff_ID)       ON DELETE RESTRICT,
    FOREIGN KEY (Table_ID)    REFERENCES TABLE_INFO(Table_ID)  ON DELETE RESTRICT
);

-- ============================================================
-- 6. ORDER_ITEM TABLE (Bridge: ORDERS contains MENU_ITEM)
-- ============================================================
CREATE TABLE IF NOT EXISTS ORDER_ITEM (
    OrderItem_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_ID     INT NOT NULL,
    Item_ID      INT NOT NULL,
    Quantity     INT NOT NULL DEFAULT 1,
    Subtotal     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (Order_ID) REFERENCES ORDERS(Order_ID)    ON DELETE CASCADE,
    FOREIGN KEY (Item_ID)  REFERENCES MENU_ITEM(Item_ID)  ON DELETE RESTRICT
);

-- ============================================================
-- 7. PAYMENT TABLE (Added as requested)
-- ============================================================
CREATE TABLE IF NOT EXISTS PAYMENT (
    Payment_ID     INT AUTO_INCREMENT PRIMARY KEY,
    Order_ID       INT NOT NULL UNIQUE,
    Amount         DECIMAL(10,2) NOT NULL,
    Payment_Method ENUM('Cash','Card','UPI','Online') NOT NULL DEFAULT 'Cash',
    Transaction_ID VARCHAR(100),
    Payment_Date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status         ENUM('Pending','Success','Failed','Refunded') DEFAULT 'Pending',
    Notes          TEXT,
    FOREIGN KEY (Order_ID) REFERENCES ORDERS(Order_ID) ON DELETE CASCADE
);

-- ============================================================
-- SAMPLE DATA - Menu Items
-- ============================================================
INSERT INTO MENU_ITEM (Item_Name, Price, Category, Description, Rating, Times_Ordered) VALUES
('Paneer Tikka',        220.00, 'Starter',      'Grilled cottage cheese with spices',       4.5, 120),
('Veg Spring Rolls',    150.00, 'Starter',      'Crispy rolls with mixed vegetables',        4.2,  95),
('Chicken 65',          280.00, 'Starter',      'Spicy deep-fried chicken appetizer',        4.7, 200),
('Masala Dosa',         160.00, 'Main Course',  'Crispy rice crepe with potato filling',     4.6, 180),
('Butter Chicken',      350.00, 'Main Course',  'Creamy tomato-based chicken curry',         4.8, 300),
('Dal Makhani',         240.00, 'Main Course',  'Slow-cooked black lentils in cream',        4.4, 150),
('Biryani (Veg)',        280.00, 'Main Course',  'Fragrant basmati rice with vegetables',     4.3, 130),
('Biryani (Chicken)',   350.00, 'Main Course',  'Aromatic chicken biryani',                  4.9, 400),
('Gulab Jamun',          80.00, 'Dessert',      'Soft milk dumplings in sugar syrup',        4.5,  90),
('Ice Cream Sundae',    150.00, 'Dessert',      'Three-scoop ice cream with toppings',       4.6,  80),
('Mango Lassi',         120.00, 'Beverage',     'Chilled mango yogurt drink',                4.7, 110),
('Fresh Lime Soda',      80.00, 'Beverage',     'Refreshing lime soda with mint',            4.3,  75),
('Cold Coffee',         130.00, 'Beverage',     'Blended cold coffee with cream',            4.4,  60),
('Naan',                 50.00, 'Snack',        'Leavened flatbread from tandoor',           4.5, 250),
('Family Combo',        999.00, 'Combo',        'Starter + 2 mains + 2 beverages + dessert', 4.8,  45);

-- ============================================================
-- SAMPLE DATA - Staff
-- ============================================================
INSERT INTO STAFF (Name, Role, Phone_No, Salary) VALUES
('Rajesh Kumar',   'Manager',  '9876543210', 50000.00),
('Priya Sharma',   'Waiter',   '9876543211', 20000.00),
('Amit Singh',     'Chef',     '9876543212', 35000.00),
('Anjali Verma',   'Cashier',  '9876543213', 22000.00),
('Suresh Patel',   'Waiter',   '9876543214', 20000.00);

-- ============================================================
-- SAMPLE DATA - Table Info
-- ============================================================
INSERT INTO TABLE_INFO (Capacity, Location, Status) VALUES
(2,  'Indoor',       'Available'),
(4,  'Indoor',       'Available'),
(4,  'Indoor',       'Available'),
(6,  'Outdoor',      'Available'),
(4,  'Outdoor',      'Available'),
(8,  'Rooftop',      'Available'),
(4,  'Rooftop',      'Available'),
(10, 'Private Room', 'Available');

-- ============================================================
-- SAMPLE DATA - Customers
-- ============================================================
INSERT INTO CUSTOMER (Name, Phone_No, Email, Address) VALUES
('Neha Gupta',    '9898001122', 'neha@email.com',   'Sector 15, Noida'),
('Rohit Mehta',   '9898002233', 'rohit@email.com',  'MG Road, Bangalore'),
('Sunita Joshi',  '9898003344', 'sunita@email.com', 'Banjara Hills, Hyderabad'),
('Vikram Rao',    '9898004455', 'vikram@email.com', 'Koramangala, Bangalore'),
('Meena Kapoor',  '9898005566', 'meena@email.com',  'Andheri, Mumbai');

-- ============================================================
-- SAMPLE ORDERS (for ML training data)
-- ============================================================
INSERT INTO ORDERS (Customer_ID, Staff_ID, Table_ID, Total_Price, Payment_Mode, Order_Status) VALUES
(1, 2, 1, 720.00,  'UPI',    'Completed'),
(2, 5, 3, 1050.00, 'Card',   'Completed'),
(3, 2, 4, 580.00,  'Cash',   'Completed'),
(4, 5, 6, 430.00,  'Cash',   'Completed'),
(5, 2, 2, 999.00,  'Online', 'Completed'),
(1, 5, 5, 350.00,  'UPI',    'Completed'),
(2, 2, 7, 820.00,  'Card',   'Completed'),
(3, 5, 1, 460.00,  'Cash',   'Completed');

-- ============================================================
-- SAMPLE ORDER ITEMS
-- ============================================================
INSERT INTO ORDER_ITEM (Order_ID, Item_ID, Quantity, Subtotal) VALUES
(1, 1, 1, 220.00), (1, 5, 1, 350.00), (1, 11, 1, 120.00),
(2, 3, 1, 280.00), (2, 8, 2, 700.00), (2, 12, 1, 80.00),
(3, 2, 2, 300.00), (3, 6, 1, 240.00), (3, 9, 1, 80.00),
(4, 4, 1, 160.00), (4, 14, 2, 100.00), (4, 13, 1, 130.00),
(5, 15, 1, 999.00),
(6, 5, 1, 350.00),
(7, 8, 1, 350.00), (7, 1, 1, 220.00), (7, 10, 1, 150.00), (7, 11, 1, 120.00),
(8, 4, 2, 320.00), (8, 9, 2, 160.00);

-- ============================================================
-- SAMPLE PAYMENTS
-- ============================================================
INSERT INTO PAYMENT (Order_ID, Amount, Payment_Method, Transaction_ID, Status) VALUES
(1, 720.00,  'UPI',    'UPI202401001', 'Success'),
(2, 1050.00, 'Card',   'CRD202401002', 'Success'),
(3, 580.00,  'Cash',   NULL,           'Success'),
(4, 430.00,  'Cash',   NULL,           'Success'),
(5, 999.00,  'Online', 'ONL202401005', 'Success'),
(6, 350.00,  'UPI',    'UPI202401006', 'Success'),
(7, 820.00,  'Card',   'CRD202401007', 'Success'),
(8, 460.00,  'Cash',   NULL,           'Success');

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- View: Full Order details
CREATE OR REPLACE VIEW order_details_view AS
SELECT 
    o.Order_ID, o.Order_Date, o.Order_Status, o.Total_Price, o.Payment_Mode,
    c.Name AS Customer_Name, c.Phone_No AS Customer_Phone,
    s.Name AS Staff_Name, s.Role AS Staff_Role,
    t.Table_ID, t.Location AS Table_Location
FROM ORDERS o
JOIN CUSTOMER c   ON o.Customer_ID = c.Customer_ID
JOIN STAFF s      ON o.Staff_ID   = s.Staff_ID
JOIN TABLE_INFO t ON o.Table_ID   = t.Table_ID;

-- View: Top selling items
CREATE OR REPLACE VIEW top_menu_items AS
SELECT 
    m.Item_ID, m.Item_Name, m.Category, m.Price, m.Rating, m.Times_Ordered,
    SUM(oi.Quantity) AS Total_Qty_Sold,
    SUM(oi.Subtotal) AS Total_Revenue
FROM MENU_ITEM m
LEFT JOIN ORDER_ITEM oi ON m.Item_ID = oi.Item_ID
GROUP BY m.Item_ID
ORDER BY Total_Qty_Sold DESC;

-- View: Revenue summary
CREATE OR REPLACE VIEW daily_revenue AS
SELECT 
    DATE(o.Order_Date) AS Order_Day,
    COUNT(o.Order_ID)  AS Total_Orders,
    SUM(o.Total_Price) AS Total_Revenue,
    p.Payment_Method,
    COUNT(CASE WHEN p.Status = 'Success' THEN 1 END) AS Successful_Payments
FROM ORDERS o
LEFT JOIN PAYMENT p ON o.Order_ID = p.Order_ID
GROUP BY DATE(o.Order_Date), p.Payment_Method
ORDER BY Order_Day DESC;

-- Update Times_Ordered on new ORDER_ITEM insert (Trigger)
DELIMITER $$
CREATE TRIGGER update_times_ordered
AFTER INSERT ON ORDER_ITEM
FOR EACH ROW
BEGIN
    UPDATE MENU_ITEM 
    SET Times_Ordered = Times_Ordered + NEW.Quantity
    WHERE Item_ID = NEW.Item_ID;
END$$
DELIMITER ;

SELECT 'Schema created successfully! Database is ready.' AS Status;
