-- ================================================================
-- E-WASTE RECYCLING & COLLECTION MANAGEMENT SYSTEM
-- Full MySQL/PostgreSQL Database Schema
-- Course: CSTE2201 - Database Management System
-- Authors: Rashedul Alam Noyon (ASH2201041M)
--          Khan Md. Omar Faruqe (ASH2301022M)
-- ================================================================

-- Create & use database
CREATE DATABASE IF NOT EXISTS ewaste_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ewaste_db;

-- ================================================================
-- TABLE 1: Admin
-- ================================================================
CREATE TABLE Admin (
    AdminID     INT PRIMARY KEY AUTO_INCREMENT,
    Username    VARCHAR(50) NOT NULL UNIQUE,
    Password    VARCHAR(255) NOT NULL,  -- store hashed (bcrypt)
    Email       VARCHAR(100) NOT NULL UNIQUE,
    FullName    VARCHAR(100),
    CreatedAt   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- TABLE 2: Donor (Users)
-- ================================================================
CREATE TABLE Donor (
    DonorID          INT PRIMARY KEY AUTO_INCREMENT,
    FirstName        VARCHAR(50) NOT NULL,
    LastName         VARCHAR(50),
    Email            VARCHAR(100) NOT NULL UNIQUE,
    Phone            VARCHAR(20),
    Address          TEXT,
    PasswordHash     VARCHAR(255),          -- NULL if using OAuth
    GoogleID         VARCHAR(100) UNIQUE,   -- Google OAuth sub ID
    AuthProvider     ENUM('local','google') DEFAULT 'local',
    RegistrationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    IsActive         BOOLEAN DEFAULT TRUE
);

-- ================================================================
-- TABLE 3: Collection Center
-- ================================================================
CREATE TABLE CollectionCenter (
    CenterID    INT PRIMARY KEY AUTO_INCREMENT,
    Name        VARCHAR(100) NOT NULL,
    Location    VARCHAR(200) NOT NULL,
    ContactInfo VARCHAR(100),
    Capacity    INT DEFAULT 1000,          -- max items capacity
    CurrentLoad INT DEFAULT 0,
    IsActive    BOOLEAN DEFAULT TRUE
);

-- ================================================================
-- TABLE 4: Recycler
-- ================================================================
CREATE TABLE Recycler (
    RecyclerID     INT PRIMARY KEY AUTO_INCREMENT,
    Name           VARCHAR(100) NOT NULL,
    ContactInfo    VARCHAR(100),
    Specialization VARCHAR(100),           -- e.g. 'Mobile Phones', 'Batteries'
    Capacity       INT DEFAULT 500,
    IsActive       BOOLEAN DEFAULT TRUE
);

-- ================================================================
-- TABLE 5: Product Catalog (what we accept)
-- ================================================================
CREATE TABLE Product (
    ProductID   INT PRIMARY KEY AUTO_INCREMENT,
    Name        VARCHAR(150) NOT NULL,
    Category    ENUM('Mobile','Laptop','TV','Battery','Appliance','Printer','Camera','Gaming','Other') NOT NULL,
    Emoji       VARCHAR(10),
    Description TEXT,
    MinPrice    DECIMAL(10,2),
    MaxPrice    DECIMAL(10,2),
    Condition   ENUM('Any','Good','Fair','Poor') DEFAULT 'Any',
    IsActive    BOOLEAN DEFAULT TRUE
);

-- ================================================================
-- TABLE 6: E-Waste Item (submitted by donor)
-- ================================================================
CREATE TABLE EWasteItem (
    ItemID           INT PRIMARY KEY AUTO_INCREMENT,
    DonorID          INT NOT NULL,
    ProductID        INT,                  -- what type of product
    ItemName         VARCHAR(150) NOT NULL,
    Category         VARCHAR(50) NOT NULL,
    Description      TEXT,
    Condition        ENUM('Good','Fair','Poor') NOT NULL,
    Quantity         INT DEFAULT 1,
    SubmissionDate   DATE NOT NULL,
    Status           ENUM('Pending','Collected','Recycled','Rejected') DEFAULT 'Pending',
    EstimatedPrice   DECIMAL(10,2),        -- set by admin during negotiation
    FinalPrice       DECIMAL(10,2),        -- agreed price
    FOREIGN KEY (DonorID) REFERENCES Donor(DonorID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID) ON DELETE SET NULL
);

-- ================================================================
-- TABLE 7: Collection (links Item → Center)
-- ================================================================
CREATE TABLE Collection (
    CollectionID   INT PRIMARY KEY AUTO_INCREMENT,
    ItemID         INT NOT NULL UNIQUE,    -- 1:1 with EWasteItem
    CenterID       INT NOT NULL,
    CollectionDate DATE,
    Status         ENUM('Scheduled','Collected','Failed') DEFAULT 'Scheduled',
    Notes          TEXT,
    FOREIGN KEY (ItemID) REFERENCES EWasteItem(ItemID) ON DELETE CASCADE,
    FOREIGN KEY (CenterID) REFERENCES CollectionCenter(CenterID)
);

-- ================================================================
-- TABLE 8: Recycling Process
-- ================================================================
CREATE TABLE RecyclingProcess (
    ProcessID   INT PRIMARY KEY AUTO_INCREMENT,
    ItemID      INT NOT NULL,
    RecyclerID  INT NOT NULL,
    ProcessType ENUM('Sorting','Dismantling','Refurbishing','Shredding','Disposal') NOT NULL,
    ProcessDate DATE,
    Status      ENUM('In Progress','Completed','Failed') DEFAULT 'In Progress',
    Notes       TEXT,
    FOREIGN KEY (ItemID) REFERENCES EWasteItem(ItemID) ON DELETE CASCADE,
    FOREIGN KEY (RecyclerID) REFERENCES Recycler(RecyclerID)
);

-- ================================================================
-- TABLE 9: Messages (Donor ↔ Admin Chat)
-- ================================================================
CREATE TABLE Message (
    MessageID  INT PRIMARY KEY AUTO_INCREMENT,
    SenderType ENUM('admin','donor') NOT NULL,
    SenderID   INT NOT NULL,
    ReceiverType ENUM('admin','donor') NOT NULL,
    ReceiverID INT NOT NULL,
    MessageText TEXT NOT NULL,
    IsRead     BOOLEAN DEFAULT FALSE,
    SentAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Optional: link message to a specific item
    RelatedItemID INT,
    FOREIGN KEY (RelatedItemID) REFERENCES EWasteItem(ItemID) ON DELETE SET NULL
);

-- ================================================================
-- TABLE 10: Notification
-- ================================================================
CREATE TABLE Notification (
    NotificationID INT PRIMARY KEY AUTO_INCREMENT,
    UserType       ENUM('admin','donor') NOT NULL,
    UserID         INT NOT NULL,
    Title          VARCHAR(200),
    Body           TEXT,
    IsRead         BOOLEAN DEFAULT FALSE,
    CreatedAt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INDEXES for performance
-- ================================================================
CREATE INDEX idx_item_donor    ON EWasteItem(DonorID);
CREATE INDEX idx_item_status   ON EWasteItem(Status);
CREATE INDEX idx_msg_sender    ON Message(SenderType, SenderID);
CREATE INDEX idx_msg_receiver  ON Message(ReceiverType, ReceiverID);
CREATE INDEX idx_collection_center ON Collection(CenterID);
CREATE INDEX idx_recycle_item  ON RecyclingProcess(ItemID);

-- ================================================================
-- SAMPLE DATA
-- ================================================================

-- Admin
INSERT INTO Admin (Username, Password, Email, FullName) VALUES
('admin', '$2b$12$hashedpassword', 'admin@ecoloop.com', 'EcoLoop Admin');

-- Donors
INSERT INTO Donor (FirstName, LastName, Email, Phone, Address, PasswordHash) VALUES
('Rashedul', 'Noyon', 'rashedul@gmail.com', '+880 17 1234 5678', 'Mirpur, Dhaka', '$2b$12$hash1'),
('Omar', 'Faruqe', 'omar@gmail.com', '+880 18 9876 5432', 'Gulshan, Dhaka', '$2b$12$hash2'),
('Fatima', 'Begum', 'fatima@gmail.com', '+880 19 1111 2222', 'Uttara, Dhaka', '$2b$12$hash3'),
('Karim', 'Rahman', 'karim@gmail.com', '+880 17 3333 4444', 'Motijheel, Dhaka', '$2b$12$hash4');

-- Collection Centers
INSERT INTO CollectionCenter (Name, Location, ContactInfo, Capacity) VALUES
('Dhaka Central Collection Center', 'Mirpur-10, Dhaka', '01700-000001', 2000),
('Gulshan E-Waste Hub', 'Gulshan-2, Dhaka', '01700-000002', 1500),
('Uttara Green Point', 'Uttara Sector 10, Dhaka', '01700-000003', 1000),
('Motijheel Drop Zone', 'Motijheel, Dhaka', '01700-000004', 800),
('Chittagong Eco Center', 'GEC Circle, Chittagong', '01700-000005', 1200);

-- Recyclers
INSERT INTO Recycler (Name, ContactInfo, Specialization, Capacity) VALUES
('GreenTech Recyclers Ltd', '01800-111111', 'Mobile Phones, Tablets', 500),
('Bangladesh Metal Recovery', '01800-222222', 'Batteries, Metal Components', 800),
('EcoCycle BD', '01800-333333', 'Laptops, Desktops', 600),
('CleanElec Solutions', '01800-444444', 'Appliances, TVs', 700);

-- Products
INSERT INTO Product (Name, Category, Emoji, Description, MinPrice, MaxPrice, Condition) VALUES
('Smartphone (Any Brand)', 'Mobile', '📱', 'Used or broken mobile phones', 200.00, 2500.00, 'Any'),
('Laptop / Notebook', 'Laptop', '💻', 'Old laptops, working or not', 500.00, 8000.00, 'Good'),
('LCD / LED Monitor', 'TV', '🖥️', 'Flat screen monitors 15–32 inch', 300.00, 3000.00, 'Fair'),
('CRT Television', 'TV', '📺', 'Old tube TVs', 100.00, 500.00, 'Poor'),
('Lithium Batteries', 'Battery', '🔋', 'Li-ion, Li-Po batteries', 50.00, 300.00, 'Any'),
('Lead Acid Battery', 'Battery', '⚡', 'Car, IPS, motorcycle batteries', 200.00, 1500.00, 'Any'),
('Inkjet / Laser Printer', 'Printer', '🖨️', 'Desktop printers any brand', 150.00, 2000.00, 'Fair'),
('Digital Camera', 'Camera', '📷', 'Point & shoot, DSLR, action cameras', 500.00, 5000.00, 'Good'),
('Refrigerator / Fridge', 'Appliance', '🧊', 'Single/double door fridges', 1000.00, 6000.00, 'Fair'),
('Washing Machine', 'Appliance', '🫧', 'Top or front loading', 800.00, 4000.00, 'Fair'),
('Air Conditioner', 'Appliance', '❄️', 'Window or split AC units', 1500.00, 10000.00, 'Good'),
('Desktop Computer (Full Set)', 'Laptop', '🖥️', 'CPU + monitor + keyboard', 500.00, 5000.00, 'Fair'),
('Gaming Console', 'Gaming', '🎮', 'PlayStation, Xbox, Nintendo', 1000.00, 15000.00, 'Good'),
('Tablet / iPad', 'Mobile', '📟', 'Android tablets, iPads', 300.00, 5000.00, 'Good'),
('Microwave Oven', 'Appliance', '🍽️', 'All sizes, broken or not', 300.00, 2000.00, 'Fair'),
('Router / Modem', 'Mobile', '📡', 'WiFi routers, DSL modems', 50.00, 300.00, 'Any'),
('Power Bank', 'Battery', '🔌', 'External battery packs', 100.00, 800.00, 'Fair'),
('Smart Watch', 'Mobile', '⌚', 'Fitness bands, smartwatches', 200.00, 3000.00, 'Good'),
('Keyboard & Mouse', 'Laptop', '⌨️', 'Wired or wireless, any type', 50.00, 400.00, 'Any'),
('Electric Fan', 'Appliance', '💨', 'Table, ceiling, or stand fans', 80.00, 500.00, 'Any');

-- E-Waste Items
INSERT INTO EWasteItem (DonorID, ItemName, Category, Description, Condition, Quantity, SubmissionDate, Status) VALUES
(1, 'iPhone 8', 'Mobile', 'Screen cracked, battery OK. IMEI: 352099001761481', 'Good', 1, '2025-01-15', 'Collected'),
(2, 'Dell Inspiron 15', 'Laptop', 'Slow, old model, 4GB RAM', 'Fair', 1, '2025-01-20', 'Pending'),
(1, 'AA Battery Pack x20', 'Battery', 'Expired AA batteries from remote controls', 'Poor', 20, '2025-02-01', 'Recycled'),
(3, 'Samsung 32" LED TV', 'TV', 'Backlight broken', 'Fair', 1, '2025-02-05', 'Collected'),
(4, 'Epson L3110 Printer', 'Printer', 'Paper jam issue, otherwise fine', 'Good', 1, '2025-02-10', 'Pending');

-- Collections
INSERT INTO Collection (ItemID, CenterID, CollectionDate, Status) VALUES
(1, 1, '2025-01-17', 'Collected'),
(3, 2, '2025-02-03', 'Collected'),
(4, 1, '2025-02-07', 'Collected');

-- Recycling Process
INSERT INTO RecyclingProcess (ItemID, RecyclerID, ProcessType, ProcessDate, Status) VALUES
(3, 2, 'Disposal', '2025-02-05', 'Completed'),
(1, 1, 'Dismantling', '2025-01-20', 'Completed');

-- Messages
INSERT INTO Message (SenderType, SenderID, ReceiverType, ReceiverID, MessageText, RelatedItemID) VALUES
('donor', 1, 'admin', 1, 'Hello! I submitted an iPhone 8. What is the current price for this condition?', 1),
('admin', 1, 'donor', 1, 'Hi Rashedul! For iPhone 8 in Good condition, we offer ৳800–1200. Can you confirm the IMEI?', 1),
('donor', 1, 'admin', 1, 'IMEI: 352099001761481. Please confirm pickup.', 1),
('donor', 2, 'admin', 1, 'I have a Dell laptop. Is ৳3000 okay for it?', 2),
('admin', 1, 'donor', 2, 'Hi Omar! For your Dell Inspiron in Fair condition, we can offer ৳1500-2500. Please bring it to Gulshan center.', 2);

-- ================================================================
-- USEFUL QUERIES
-- ================================================================

-- 1. Top 5 most recycled categories
SELECT Category, COUNT(*) AS TotalItems
FROM EWasteItem
WHERE Status = 'Recycled'
GROUP BY Category
ORDER BY TotalItems DESC
LIMIT 5;

-- 2. Monthly e-waste collection stats
SELECT 
    YEAR(SubmissionDate) AS Year,
    MONTH(SubmissionDate) AS Month,
    COUNT(*) AS TotalSubmissions,
    SUM(CASE WHEN Status='Recycled' THEN 1 ELSE 0 END) AS Recycled
FROM EWasteItem
GROUP BY Year, Month
ORDER BY Year DESC, Month DESC;

-- 3. Donor activity report
SELECT 
    d.DonorID,
    CONCAT(d.FirstName, ' ', d.LastName) AS DonorName,
    d.Address AS Zone,
    COUNT(e.ItemID) AS TotalSubmissions,
    SUM(CASE WHEN e.Status='Recycled' THEN 1 ELSE 0 END) AS RecycledItems
FROM Donor d
LEFT JOIN EWasteItem e ON d.DonorID = e.DonorID
GROUP BY d.DonorID
ORDER BY TotalSubmissions DESC;

-- 4. Collection center load
SELECT 
    cc.Name,
    cc.Location,
    cc.Capacity,
    COUNT(c.CollectionID) AS ItemsHandled
FROM CollectionCenter cc
LEFT JOIN Collection c ON cc.CenterID = c.CenterID
GROUP BY cc.CenterID;

-- 5. Recycler efficiency report
SELECT 
    r.Name AS RecyclerName,
    r.Specialization,
    COUNT(rp.ProcessID) AS TotalProcessed,
    SUM(CASE WHEN rp.Status='Completed' THEN 1 ELSE 0 END) AS Completed
FROM Recycler r
LEFT JOIN RecyclingProcess rp ON r.RecyclerID = rp.RecyclerID
GROUP BY r.RecyclerID;

-- 6. Unread messages for admin
SELECT 
    m.MessageID,
    CONCAT(d.FirstName, ' ', d.LastName) AS FromDonor,
    m.MessageText,
    m.SentAt,
    e.ItemName AS RelatedItem
FROM Message m
JOIN Donor d ON m.SenderID = d.DonorID AND m.SenderType = 'donor'
LEFT JOIN EWasteItem e ON m.RelatedItemID = e.ItemID
WHERE m.ReceiverType = 'admin' AND m.IsRead = FALSE
ORDER BY m.SentAt DESC;

-- 7. Items pending more than 7 days
SELECT e.ItemID, e.ItemName, e.Category,
       CONCAT(d.FirstName, ' ', d.LastName) AS Donor,
       e.SubmissionDate,
       DATEDIFF(CURDATE(), e.SubmissionDate) AS DaysPending
FROM EWasteItem e
JOIN Donor d ON e.DonorID = d.DonorID
WHERE e.Status = 'Pending'
AND DATEDIFF(CURDATE(), e.SubmissionDate) > 7
ORDER BY DaysPending DESC;
