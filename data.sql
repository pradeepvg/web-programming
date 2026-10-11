-- Smart Home Expense & Maintenance Tracker
-- Demo Seed Data (Indian Household in INR)

USE smarthome_db;

-- 1. Demo User: Rahul Sharma (Password: demo123 - BCrypt hashed: $2a$10$779L.y624rIekQ3O5xP7.OuD53448UaVv9gT9mZ2XlQ3l1K.l3a1C)
INSERT INTO users (id, name, email, password_hash, phone, address, currency)
VALUES (1, 'Rahul Sharma', 'rahul.sharma@example.in', '$2a$10$779L.y624rIekQ3O5xP7.OuD53448UaVv9gT9mZ2XlQ3l1K.l3a1C', '+91 98765 43210', 'Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103', 'INR')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 2. Service Providers
INSERT INTO service_providers (id, user_id, company_name, technician_name, service_category, contact_number, email, address, service_notes)
VALUES
(1, 1, 'QuickFix Plumbing Solutions', 'Ramesh Kumar', 'Plumbing', '+91 98450 11223', 'ramesh@quickfixplumbing.in', 'Indiranagar 100ft Road, Bengaluru', 'Specializes in bathroom piping, leakage repairs, and geyser fittings'),
(2, 1, 'CoolBreeze Aircon Care', 'Suresh Nair', 'Air conditioning', '+91 97422 33445', 'service@coolbreezeair.in', 'HSR Layout Sector 2, Bengaluru', 'Authorized Daikin and Voltas technician for quarterly deep cleaning and gas top-up'),
(3, 1, 'VoltGuard Electricals', 'Mahesh Patil', 'Electrical', '+91 99011 55667', 'mahesh@voltguard.com', 'Koramangala 4th Block, Bengaluru', 'Licensed electrician for MCB repairs, smart switches, and inverter maintenance'),
(4, 1, 'PureDrop Water RO Care', 'Dinesh Gowda', 'Water purifier', '+91 96112 77889', 'dinesh@puredrop.in', 'BTM Layout 2nd Stage, Bengaluru', 'Kent & Aquaguard membrane replacement and sediment filter servicing'),
(5, 1, 'UrbanShield Pest Control', 'Vijay Anand', 'Pest control', '+91 98800 99001', 'support@urbanshield.in', 'Whitefield Main Road, Bengaluru', 'Organic herbal pest control for termites, cockroaches, and bed bugs')
ON DUPLICATE KEY UPDATE company_name=VALUES(company_name);

-- 3. Monthly Budget (e.g. ₹15,000 for current month 2026-10)
INSERT INTO budgets (id, user_id, month_year, total_budget)
VALUES (1, 1, '2026-10', 15000.00)
ON DUPLICATE KEY UPDATE total_budget=VALUES(total_budget);

INSERT INTO category_budgets (id, budget_id, category, budget_limit)
VALUES
(1, 1, 'Electricity', 2500.00),
(2, 1, 'Groceries', 6000.00),
(3, 1, 'Water', 800.00),
(4, 1, 'Internet', 1200.00),
(5, 1, 'Plumbing', 1500.00),
(6, 1, 'Air conditioning', 2000.00),
(7, 1, 'Gas', 1000.00)
ON DUPLICATE KEY UPDATE budget_limit=VALUES(budget_limit);

-- 4. Expenses (Demonstrating positive values, various categories & payment methods)
INSERT INTO expenses (id, user_id, title, description, category, amount, expense_date, payment_method, vendor)
VALUES
(1, 1, 'BESCOM Monthly Electricity Bill', 'October power consumption charges for home', 'Electricity', 1850.00, '2026-10-03', 'UPI', 'BESCOM Bengaluru'),
(2, 1, 'BWSSB Water Supply Charges', 'Monthly piped municipal water supply', 'Water', 650.00, '2026-10-04', 'Net Banking', 'BWSSB'),
(3, 1, 'Kitchen Sink Pipe Replacement', 'Emergency plumbing replacement for leaking PVC connector', 'Plumbing', 1200.00, '2026-10-05', 'UPI', 'QuickFix Plumbing Solutions'),
(4, 1, 'Airtel Xstream Fiber Broadband', '100 Mbps unlimited home fiber wifi plan', 'Internet', 999.00, '2026-10-02', 'Credit Card', 'Airtel Telecommunications'),
(5, 1, 'Weekly Organic Grocery Purchase', 'Vegetables, milk, pulses and monthly cooking oil', 'Groceries', 3450.00, '2026-10-06', 'UPI', 'Blinkit Superstore'),
(6, 1, 'Indane LPG Gas Cylinder Refill', '14.2 kg domestic cooking gas cylinder refill', 'Gas', 850.00, '2026-10-01', 'UPI', 'Indane Gas Agency'),
(7, 1, 'Hall Split AC Deep Servicing', 'Pre-festival chemical wash and coil cleaning', 'Air conditioning', 1500.00, '2026-10-07', 'Cash', 'CoolBreeze Aircon Care'),
(8, 1, 'Philips LED Bulbs & MCB Switch', 'Replacement for balcony and kitchen fixtures', 'Electrical repairs', 620.00, '2026-10-08', 'UPI', 'VoltGuard Electricals')
ON DUPLICATE KEY UPDATE amount=VALUES(amount);

-- 5. Household Bills
INSERT INTO bills (id, user_id, title, category, amount, billing_period, issue_date, due_date, status, payment_date, reference_number, payment_method)
VALUES
(1, 1, 'Electricity (BESCOM)', 'Electricity', 1850.00, 'Oct 2026', '2026-10-01', '2026-10-15', 'PAID', '2026-10-03', 'UPI-9871234455', 'UPI'),
(2, 1, 'Airtel Fiber Broadband', 'Internet', 999.00, 'Oct 2026', '2026-10-01', '2026-10-10', 'PAID', '2026-10-02', 'TXN-88776655', 'Credit Card'),
(3, 1, 'Society Maintenance Charges', 'Maintenance charges', 3500.00, 'Oct 2026', '2026-10-05', '2026-10-20', 'UNPAID', NULL, NULL, NULL),
(4, 1, 'Municipal Water Bill (BWSSB)', 'Water', 650.00, 'Oct 2026', '2026-10-02', '2026-10-18', 'PAID', '2026-10-04', 'NEFT-5544332211', 'Net Banking'),
(5, 1, 'HDFC Home Loan EMI', 'Home loan', 28500.00, 'Oct 2026', '2026-10-01', '2026-10-10', 'OVERDUE', NULL, NULL, NULL),
(6, 1, 'Piped Natural Gas (GAIL Gas)', 'Gas', 480.00, 'Sep-Oct 2026', '2026-10-08', '2026-10-25', 'UNPAID', NULL, NULL, NULL)
ON DUPLICATE KEY UPDATE amount=VALUES(amount);

-- 6. Bill Payments
INSERT INTO bill_payments (id, bill_id, user_id, amount_paid, payment_date, payment_method, reference_number, notes)
VALUES
(1, 1, 1, 1850.00, '2026-10-03', 'UPI', 'UPI-9871234455', 'Paid via GooglePay to BESCOM account'),
(2, 2, 1, 999.00, '2026-10-02', 'Credit Card', 'TXN-88776655', 'Auto-debited on ICICI Amazon Pay Card'),
(3, 4, 1, 650.00, '2026-10-04', 'Net Banking', 'NEFT-5544332211', 'Paid via HDFC NetBanking')
ON DUPLICATE KEY UPDATE amount_paid=VALUES(amount_paid);

-- 7. Maintenance Tasks
INSERT INTO maintenance_tasks (id, user_id, service_provider_id, title, description, category, priority, status, scheduled_date, due_date, completion_date, estimated_cost, actual_cost, notes)
VALUES
(1, 1, 4, 'RO Water Purifier Filter Replacement', 'Replace carbon filter and RO membrane cartridge for sediment purity', 'Water purifier', 'HIGH', 'COMPLETED', '2026-10-05', '2026-10-07', '2026-10-06', 1500.00, 1400.00, 'Serviced by Dinesh. Next service scheduled in 6 months.'),
(2, 1, 2, 'Master Bedroom Split AC Servicing', 'Air filter wash, coolant pressure inspection and blower lubrication', 'Air conditioning', 'MEDIUM', 'IN_PROGRESS', '2026-10-10', '2026-10-12', NULL, 1200.00, 0.00, 'Suresh Nair confirmed visit for this evening.'),
(3, 1, 3, 'Main Distribution Board & Inverter Check', 'Inspect inverter battery water level and terminal corrosion', 'Electrical', 'HIGH', 'OVERDUE', '2026-10-02', '2026-10-05', NULL, 800.00, 0.00, 'Overdue inspection. Urgent attention needed to avoid power outage.'),
(4, 1, 1, 'Bathroom Concealed Diverter Leak Fix', 'Fix slow dripping tap in master bathroom shower unit', 'Plumbing', 'URGENT', 'PENDING', '2026-10-12', '2026-10-14', NULL, 1200.00, 0.00, 'Technician visit scheduled for tomorrow morning.'),
(5, 1, 5, 'Herbal Kitchen & Wardrobe Pest Control', 'Comprehensive pest eradication treatment before Diwali', 'Pest control', 'LOW', 'PENDING', '2026-10-22', '2026-10-25', NULL, 2200.00, 0.00, 'Annual preventive maintenance.')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 8. Recurring Maintenance Schedules
INSERT INTO maintenance_schedules (id, user_id, title, category, frequency, preferred_day_of_month, next_due_date, estimated_cost, service_provider_id, notes, is_active)
VALUES
(1, 1, 'Quarterly AC Cleaning & Gas Check', 'Air conditioning', 'QUARTERLY', 10, '2027-01-10', 1500.00, 2, 'Scheduled every 3 months for all 2 AC units', TRUE),
(2, 1, 'RO Water Purifier Membrane Check', 'Water purifier', 'MONTHLY', 5, '2026-11-05', 450.00, 4, 'Check TDS levels and sediment filter monthly', TRUE),
(3, 1, 'Electrical Inverter Battery Inspection', 'Electrical', 'HALF_YEARLY', 15, '2027-04-15', 600.00, 3, 'Top up distilled water in tubular batteries', TRUE),
(4, 1, 'Annual Painting & Waterproofing Inspection', 'Painting', 'ANNUAL', 1, '2027-10-01', 5000.00, NULL, 'Check exterior walls and roof terrace for dampness', TRUE)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 9. Notifications
INSERT INTO notifications (id, user_id, title, message, type, is_read, action_url)
VALUES
(1, 1, 'Budget Alert: 74% Utilized', 'You have spent ₹11,119 of your ₹15,000 monthly budget.', 'WARNING', FALSE, 'budgets.html'),
(2, 1, 'Task Overdue: Inverter Inspection', 'Maintenance task "Main Distribution Board & Inverter Check" was due on 05 Oct 2026.', 'ALERT', FALSE, 'maintenance.html'),
(3, 1, 'Upcoming Bill Reminder', 'Society Maintenance Charges of ₹3,500 is due on 20 Oct 2026.', 'INFO', FALSE, 'bills.html'),
(4, 1, 'Maintenance Completed', 'RO Water Purifier Filter Replacement was marked completed by technician.', 'SUCCESS', TRUE, 'maintenance.html')
ON DUPLICATE KEY UPDATE title=VALUES(title);
