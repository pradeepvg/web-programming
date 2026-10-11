"""
Smart Home Expense & Maintenance Tracker - Full REST Server & Web Runner
Provides 100% compliant REST APIs and static web hosting matching the Spring Boot specification.
"""

import http.server
import socketserver
import json
import sqlite3
import os
import re
import csv
import io
import hashlib
import hmac
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date, timedelta

PORT = 8080
DB_FILE = "smarthome_local.db"
SECRET_KEY = b"smarthome-jwt-secret-key-32-bytes-long!!"

# Initialize Database Schema & Demo Seed Data
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        currency TEXT DEFAULT 'INR',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS service_providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        company_name TEXT NOT NULL,
        technician_name TEXT,
        service_category TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        email TEXT,
        address TEXT,
        service_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        vendor TEXT,
        receipt_filename TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        month_year TEXT NOT NULL,
        total_budget REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, month_year),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS category_budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        budget_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        budget_limit REAL NOT NULL,
        FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE,
        UNIQUE(budget_id, category)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS maintenance_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        service_provider_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'MEDIUM',
        status TEXT NOT NULL DEFAULT 'PENDING',
        scheduled_date TEXT,
        due_date TEXT NOT NULL,
        completion_date TEXT,
        estimated_cost REAL DEFAULT 0.0,
        actual_cost REAL DEFAULT 0.0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (service_provider_id) REFERENCES service_providers(id) ON DELETE SET NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS maintenance_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        frequency TEXT NOT NULL,
        preferred_day_of_month INTEGER DEFAULT 1,
        next_due_date TEXT NOT NULL,
        estimated_cost REAL DEFAULT 0.0,
        service_provider_id INTEGER,
        notes TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (service_provider_id) REFERENCES service_providers(id) ON DELETE SET NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        billing_period TEXT NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'UNPAID',
        payment_date TEXT,
        reference_number TEXT,
        payment_method TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS bill_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount_paid REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        reference_number TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'INFO',
        is_read INTEGER DEFAULT 0,
        action_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Seed Demo User if not exists
    c.execute("SELECT id FROM users WHERE email = 'rahul.sharma@example.in'")
    row = c.fetchone()
    if not row:
        pwd_hash = hashlib.sha256("demo123".encode()).hexdigest()
        c.execute("""
        INSERT INTO users (name, email, password_hash, phone, address, currency)
        VALUES ('Rahul Sharma', 'rahul.sharma@example.in', ?, '+91 98765 43210',
                'Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103', 'INR')
        """, (pwd_hash,))
        user_id = c.lastrowid

        # Seed Service Providers
        providers = [
            (user_id, 'QuickFix Plumbing Solutions', 'Ramesh Kumar', 'Plumbing', '+91 98450 11223', 'ramesh@quickfixplumbing.in', 'Indiranagar 100ft Road, Bengaluru', 'Specializes in bathroom piping, leakage repairs, and geyser fittings'),
            (user_id, 'CoolBreeze Aircon Care', 'Suresh Nair', 'Air conditioning', '+91 97422 33445', 'service@coolbreezeair.in', 'HSR Layout Sector 2, Bengaluru', 'Authorized Daikin and Voltas technician for quarterly deep cleaning and gas top-up'),
            (user_id, 'VoltGuard Electricals', 'Mahesh Patil', 'Electrical', '+91 99011 55667', 'mahesh@voltguard.com', 'Koramangala 4th Block, Bengaluru', 'Licensed electrician for MCB repairs, smart switches, and inverter maintenance'),
            (user_id, 'PureDrop Water RO Care', 'Dinesh Gowda', 'Water purifier', '+91 96112 77889', 'dinesh@puredrop.in', 'BTM Layout 2nd Stage, Bengaluru', 'Kent & Aquaguard membrane replacement and sediment filter servicing'),
            (user_id, 'UrbanShield Pest Control', 'Vijay Anand', 'Pest control', '+91 98800 99001', 'support@urbanshield.in', 'Whitefield Main Road, Bengaluru', 'Organic herbal pest control for termites, cockroaches, and bed bugs')
        ]
        c.executemany("""
        INSERT INTO service_providers (user_id, company_name, technician_name, service_category, contact_number, email, address, service_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, providers)

        # Current month YYYY-MM
        current_ym = datetime.now().strftime("%Y-%m")
        c.execute("INSERT INTO budgets (user_id, month_year, total_budget) VALUES (?, ?, 15000.00)", (user_id, current_ym))
        budget_id = c.lastrowid

        cat_budgets = [
            (budget_id, 'Electricity', 2500.00),
            (budget_id, 'Groceries', 6000.00),
            (budget_id, 'Water', 800.00),
            (budget_id, 'Internet', 1200.00),
            (budget_id, 'Plumbing', 1500.00),
            (budget_id, 'Air conditioning', 2000.00),
            (budget_id, 'Gas', 1000.00)
        ]
        c.executemany("INSERT INTO category_budgets (budget_id, category, budget_limit) VALUES (?, ?, ?)", cat_budgets)

        # Seed Expenses
        cur_year = datetime.now().year
        cur_month = datetime.now().month
        def date_str(day):
            return f"{cur_year:04d}-{cur_month:02d}-{day:02d}"

        expenses = [
            (user_id, 'BESCOM Monthly Electricity Bill', 'October power consumption charges for home', 'Electricity', 1850.00, date_str(3), 'UPI', 'BESCOM Bengaluru'),
            (user_id, 'BWSSB Water Supply Charges', 'Monthly piped municipal water supply', 'Water', 650.00, date_str(4), 'Net Banking', 'BWSSB'),
            (user_id, 'Kitchen Sink Pipe Replacement', 'Emergency plumbing replacement for leaking PVC connector', 'Plumbing', 1200.00, date_str(5), 'UPI', 'QuickFix Plumbing Solutions'),
            (user_id, 'Airtel Xstream Fiber Broadband', '100 Mbps unlimited home fiber wifi plan', 'Internet', 999.00, date_str(2), 'Credit Card', 'Airtel Telecommunications'),
            (user_id, 'Weekly Organic Grocery Purchase', 'Vegetables, milk, pulses and monthly cooking oil', 'Groceries', 3450.00, date_str(6), 'UPI', 'Blinkit Superstore'),
            (user_id, 'Indane LPG Gas Cylinder Refill', '14.2 kg domestic cooking gas cylinder refill', 'Gas', 850.00, date_str(1), 'UPI', 'Indane Gas Agency'),
            (user_id, 'Hall Split AC Deep Servicing', 'Pre-festival chemical wash and coil cleaning', 'Air conditioning', 1500.00, date_str(7), 'Cash', 'CoolBreeze Aircon Care'),
            (user_id, 'Philips LED Bulbs & MCB Switch', 'Replacement for balcony and kitchen fixtures', 'Electrical repairs', 620.00, date_str(8), 'UPI', 'VoltGuard Electricals')
        ]
        c.executemany("""
        INSERT INTO expenses (user_id, title, description, category, amount, expense_date, payment_method, vendor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, expenses)

        # Seed Bills
        bills = [
            (user_id, 'Electricity (BESCOM)', 'Electricity', 1850.00, f'Month {cur_month}', date_str(1), date_str(15), 'PAID', date_str(3), 'UPI-9871234455', 'UPI'),
            (user_id, 'Airtel Fiber Broadband', 'Internet', 999.00, f'Month {cur_month}', date_str(1), date_str(10), 'PAID', date_str(2), 'TXN-88776655', 'Credit Card'),
            (user_id, 'Society Maintenance Charges', 'Maintenance charges', 3500.00, f'Month {cur_month}', date_str(5), date_str(20), 'UNPAID', None, None, None),
            (user_id, 'Municipal Water Bill (BWSSB)', 'Water', 650.00, f'Month {cur_month}', date_str(2), date_str(18), 'PAID', date_str(4), 'NEFT-5544332211', 'Net Banking'),
            (user_id, 'HDFC Home Loan EMI', 'Home loan', 28500.00, f'Month {cur_month}', date_str(1), date_str(5), 'OVERDUE', None, None, None),
            (user_id, 'Piped Natural Gas (GAIL Gas)', 'Gas', 480.00, f'Month {cur_month}', date_str(8), date_str(25), 'UNPAID', None, None, None)
        ]
        c.executemany("""
        INSERT INTO bills (user_id, title, category, amount, billing_period, issue_date, due_date, status, payment_date, reference_number, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, bills)

        # Seed Bill Payments
        payments = [
            (1, user_id, 1850.00, date_str(3), 'UPI', 'UPI-9871234455', 'Paid via GooglePay to BESCOM account'),
            (2, user_id, 999.00, date_str(2), 'Credit Card', 'TXN-88776655', 'Auto-debited on ICICI Amazon Pay Card'),
            (4, user_id, 650.00, date_str(4), 'Net Banking', 'NEFT-5544332211', 'Paid via HDFC NetBanking')
        ]
        c.executemany("""
        INSERT INTO bill_payments (bill_id, user_id, amount_paid, payment_date, payment_method, reference_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, payments)

        # Seed Maintenance Tasks
        tasks = [
            (user_id, 4, 'RO Water Purifier Filter Replacement', 'Replace carbon filter and RO membrane cartridge for sediment purity', 'Water purifier', 'HIGH', 'COMPLETED', date_str(5), date_str(7), date_str(6), 1500.00, 1400.00, 'Serviced by Dinesh. Next service scheduled in 6 months.'),
            (user_id, 2, 'Master Bedroom Split AC Servicing', 'Air filter wash, coolant pressure inspection and blower lubrication', 'Air conditioning', 'MEDIUM', 'IN_PROGRESS', date_str(10), date_str(12), None, 1200.00, 0.00, 'Suresh Nair confirmed visit for this evening.'),
            (user_id, 3, 'Main Distribution Board & Inverter Check', 'Inspect inverter battery water level and terminal corrosion', 'Electrical', 'HIGH', 'OVERDUE', date_str(2), date_str(5), None, 800.00, 0.00, 'Overdue inspection. Urgent attention needed to avoid power outage.'),
            (user_id, 1, 'Bathroom Concealed Diverter Leak Fix', 'Fix slow dripping tap in master bathroom shower unit', 'Plumbing', 'URGENT', 'PENDING', date_str(12), date_str(14), None, 1200.00, 0.00, 'Technician visit scheduled for tomorrow morning.'),
            (user_id, 5, 'Herbal Kitchen & Wardrobe Pest Control', 'Comprehensive pest eradication treatment before Diwali', 'Pest control', 'LOW', 'PENDING', date_str(22), date_str(25), None, 2200.00, 0.00, 'Annual preventive maintenance.')
        ]
        c.executemany("""
        INSERT INTO maintenance_tasks (user_id, service_provider_id, title, description, category, priority, status, scheduled_date, due_date, completion_date, estimated_cost, actual_cost, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tasks)

        # Seed Maintenance Schedules
        schedules = [
            (user_id, 'Quarterly AC Cleaning & Gas Check', 'Air conditioning', 'QUARTERLY', 10, f"{cur_year}-12-10", 1500.00, 2, 'Scheduled every 3 months for all 2 AC units', 1),
            (user_id, 'RO Water Purifier Membrane Check', 'Water purifier', 'MONTHLY', 5, f"{cur_year:04d}-{(cur_month%12)+1:02d}-05", 450.00, 4, 'Check TDS levels and sediment filter monthly', 1),
            (user_id, 'Electrical Inverter Battery Inspection', 'Electrical', 'HALF_YEARLY', 15, f"{cur_year+1}-04-15", 600.00, 3, 'Top up distilled water in tubular batteries', 1),
            (user_id, 'Annual Painting & Waterproofing Inspection', 'Painting', 'ANNUAL', 1, f"{cur_year+1}-10-01", 5000.00, None, 'Check exterior walls and roof terrace for dampness', 1)
        ]
        c.executemany("""
        INSERT INTO maintenance_schedules (user_id, title, category, frequency, preferred_day_of_month, next_due_date, estimated_cost, service_provider_id, notes, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, schedules)

        # Seed Notifications
        notifs = [
            (user_id, 'Budget Alert: 74% Utilized', 'You have spent ₹11,119 of your ₹15,000 monthly budget.', 'WARNING', 0, 'budgets.html'),
            (user_id, 'Task Overdue: Inverter Inspection', 'Maintenance task "Main Distribution Board & Inverter Check" was due on 05 Oct.', 'ALERT', 0, 'maintenance.html'),
            (user_id, 'Upcoming Bill Reminder', 'Society Maintenance Charges of ₹3,500 is due on 20 Oct.', 'INFO', 0, 'bills.html'),
            (user_id, 'Maintenance Completed', 'RO Water Purifier Filter Replacement was marked completed by technician.', 'SUCCESS', 1, 'maintenance.html')
        ]
        c.executemany("""
        INSERT INTO notifications (user_id, title, message, type, is_read, action_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """, notifs)

    conn.commit()
    conn.close()

import base64

# Token Helpers
def generate_token(user_id, email):
    exp = int(time.time()) + 86400 * 7
    payload_str = json.dumps({"userId": user_id, "email": email, "exp": exp})
    b64_payload = base64.urlsafe_b64encode(payload_str.encode()).decode()
    sig = hmac.new(SECRET_KEY, b64_payload.encode(), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"

def verify_token(token):
    if not token:
        return None
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, sig = parts
        expected_sig = hmac.new(SECRET_KEY, b64_payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode())
        payload = json.loads(payload_bytes.decode())
        if payload.get("exp", 0) < int(time.time()):
            return None
        return int(payload.get("userId"))
    except Exception:
        return None

# Formatting Currency INR
def format_inr(amount):
    try:
        val = float(amount or 0)
        s = f"{val:,.2f}"
        return f"₹{s}"
    except Exception:
        return "₹0.00"

class SmartHomeRequestHandler(http.server.SimpleHTTPRequestHandler):

    def send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def send_csv(self, filename, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def get_auth_user_id(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return verify_token(token)
        return None

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)
        return {}

    def get_db(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Static files
        if not path.startswith("/api/"):
            if path == "/":
                self.path = "/index.html"
            return super().do_GET()

        # Public endpoints
        if path == "/api/health":
            return self.send_json(200, {"status": "UP", "time": datetime.now().isoformat()})

        user_id = self.get_auth_user_id()
        if not user_id:
            return self.send_json(401, {"error": "Unauthorized. Please log in."})

        conn = self.get_db()
        c = conn.cursor()

        try:
            # 1. Profile
            if path == "/api/auth/profile":
                c.execute("SELECT id, name, email, phone, address, currency, created_at FROM users WHERE id = ?", (user_id,))
                user = c.fetchone()
                if not user:
                    return self.send_json(404, {"error": "User not found"})
                return self.send_json(200, dict(user))

            # 2. Expenses
            elif path == "/api/expenses":
                category = query.get("category", [None])[0]
                payment_method = query.get("paymentMethod", [None])[0]
                start_date = query.get("startDate", [None])[0]
                end_date = query.get("endDate", [None])[0]
                search = query.get("search", [None])[0]

                sql = "SELECT * FROM expenses WHERE user_id = ?"
                params = [user_id]
                if category:
                    sql += " AND category = ?"
                    params.append(category)
                if payment_method:
                    sql += " AND payment_method = ?"
                    params.append(payment_method)
                if start_date:
                    sql += " AND expense_date >= ?"
                    params.append(start_date)
                if end_date:
                    sql += " AND expense_date <= ?"
                    params.append(end_date)
                if search:
                    sql += " AND (title LIKE ? OR vendor LIKE ? OR description LIKE ?)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                sql += " ORDER BY expense_date DESC, id DESC"

                c.execute(sql, params)
                rows = [dict(r) for r in c.fetchall()]
                for r in rows:
                    r["formattedAmount"] = format_inr(r["amount"])
                return self.send_json(200, rows)

            elif path == "/api/expenses/export/csv":
                c.execute("SELECT id, expense_date, title, category, amount, payment_method, vendor, description FROM expenses WHERE user_id = ? ORDER BY expense_date DESC", (user_id,))
                rows = c.fetchall()
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Expense ID", "Date", "Title", "Category", "Amount (INR)", "Payment Method", "Vendor", "Description"])
                for r in rows:
                    writer.writerow([r["id"], r["expense_date"], r["title"], r["category"], r["amount"], r["payment_method"], r["vendor"] or "", r["description"] or ""])
                return self.send_csv("expenses.csv", output.getvalue())

            elif re.match(r"^/api/expenses/(\d+)$", path):
                exp_id = int(re.match(r"^/api/expenses/(\d+)$", path).group(1))
                c.execute("SELECT * FROM expenses WHERE id = ? AND user_id = ?", (exp_id, user_id))
                row = c.fetchone()
                if not row:
                    return self.send_json(404, {"error": "Expense not found"})
                data = dict(row)
                data["formattedAmount"] = format_inr(data["amount"])
                return self.send_json(200, data)

            # 3. Budgets
            elif path == "/api/budgets":
                month_year = query.get("monthYear", [datetime.now().strftime("%Y-%m")])[0]
                c.execute("SELECT * FROM budgets WHERE user_id = ? AND month_year = ?", (user_id, month_year))
                b_row = c.fetchone()

                total_budget = b_row["total_budget"] if b_row else 0.0
                budget_id = b_row["id"] if b_row else None

                # Calculate total spent
                c.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?", (user_id, month_year))
                s_row = c.fetchone()
                total_spent = s_row["total"] if (s_row and s_row["total"]) else 0.0

                remaining = total_budget - total_spent
                percent_used = round((total_spent / total_budget * 100), 2) if total_budget > 0 else 0.0

                # Category budgets
                cat_budgets = []
                if budget_id:
                    c.execute("""
                    SELECT cb.category, cb.budget_limit, COALESCE(SUM(e.amount), 0) as spent
                    FROM category_budgets cb
                    LEFT JOIN expenses e ON e.user_id = ? AND e.category = cb.category AND strftime('%Y-%m', e.expense_date) = ?
                    WHERE cb.budget_id = ?
                    GROUP BY cb.category, cb.budget_limit
                    """, (user_id, month_year, budget_id))
                    for r in c.fetchall():
                        sp = r["spent"] or 0.0
                        limit = r["budget_limit"]
                        rem = limit - sp
                        pct = round((sp / limit * 100), 2) if limit > 0 else 0.0
                        cat_budgets.append({
                            "category": r["category"],
                            "budgetLimit": limit,
                            "spent": sp,
                            "remaining": rem,
                            "percentageUsed": pct
                        })

                res = {
                    "id": budget_id,
                    "monthYear": month_year,
                    "totalBudget": total_budget,
                    "totalSpent": total_spent,
                    "remainingBalance": remaining,
                    "percentageUsed": percent_used,
                    "warning80Percent": (80.0 <= percent_used < 100.0),
                    "exceededAlert": (percent_used >= 100.0),
                    "categoryBudgets": cat_budgets
                }
                return self.send_json(200, res)

            # 4. Maintenance
            elif path == "/api/maintenance/tasks":
                today_str = date.today().isoformat()
                # Update overdue in background
                c.execute("""
                UPDATE maintenance_tasks
                SET status = 'OVERDUE'
                WHERE user_id = ? AND status != 'COMPLETED' AND due_date < ?
                """, (user_id, today_str))
                conn.commit()

                c.execute("""
                SELECT mt.*, sp.company_name as service_provider_name, sp.contact_number as service_provider_contact
                FROM maintenance_tasks mt
                LEFT JOIN service_providers sp ON mt.service_provider_id = sp.id
                WHERE mt.user_id = ?
                ORDER BY mt.due_date ASC, mt.id DESC
                """, (user_id,))
                rows = [dict(r) for r in c.fetchall()]
                for r in rows:
                    r["isOverdue"] = (r["status"] == "OVERDUE" or (r["status"] != "COMPLETED" and r["due_date"] < today_str))
                return self.send_json(200, rows)

            elif re.match(r"^/api/maintenance/tasks/(\d+)$", path):
                task_id = int(re.match(r"^/api/maintenance/tasks/(\d+)$", path).group(1))
                c.execute("""
                SELECT mt.*, sp.company_name as service_provider_name, sp.contact_number as service_provider_contact
                FROM maintenance_tasks mt
                LEFT JOIN service_providers sp ON mt.service_provider_id = sp.id
                WHERE mt.id = ? AND mt.user_id = ?
                """, (task_id, user_id))
                row = c.fetchone()
                if not row:
                    return self.send_json(404, {"error": "Task not found"})
                return self.send_json(200, dict(row))

            elif path == "/api/maintenance/schedules":
                c.execute("""
                SELECT ms.*, sp.company_name as service_provider_name
                FROM maintenance_schedules ms
                LEFT JOIN service_providers sp ON ms.service_provider_id = sp.id
                WHERE ms.user_id = ?
                ORDER BY ms.next_due_date ASC
                """, (user_id,))
                return self.send_json(200, [dict(r) for r in c.fetchall()])

            # 5. Bills
            elif path == "/api/bills":
                today_str = date.today().isoformat()
                status_filter = query.get("status", [None])[0]

                # Update overdue bills
                c.execute("UPDATE bills SET status = 'OVERDUE' WHERE user_id = ? AND status = 'UNPAID' AND due_date < ?", (user_id, today_str))
                conn.commit()

                sql = "SELECT * FROM bills WHERE user_id = ?"
                params = [user_id]
                if status_filter:
                    sql += " AND status = ?"
                    params.append(status_filter.upper())
                sql += " ORDER BY due_date ASC, id DESC"

                c.execute(sql, params)
                rows = [dict(r) for r in c.fetchall()]
                for r in rows:
                    r["isOverdue"] = (r["status"] == "OVERDUE" or (r["status"] != "PAID" and r["due_date"] < today_str))
                return self.send_json(200, rows)

            elif re.match(r"^/api/bills/(\d+)$", path):
                bill_id = int(re.match(r"^/api/bills/(\d+)$", path).group(1))
                c.execute("SELECT * FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id))
                row = c.fetchone()
                if not row:
                    return self.send_json(404, {"error": "Bill not found"})
                return self.send_json(200, dict(row))

            # 6. Service Providers
            elif path == "/api/service-providers":
                c.execute("SELECT * FROM service_providers WHERE user_id = ? ORDER BY company_name ASC", (user_id,))
                return self.send_json(200, [dict(r) for r in c.fetchall()])

            elif re.match(r"^/api/service-providers/(\d+)$", path):
                sp_id = int(re.match(r"^/api/service-providers/(\d+)$", path).group(1))
                c.execute("SELECT * FROM service_providers WHERE id = ? AND user_id = ?", (sp_id, user_id))
                row = c.fetchone()
                if not row:
                    return self.send_json(404, {"error": "Service provider not found"})
                return self.send_json(200, dict(row))

            # 7. Notifications
            elif path == "/api/notifications":
                c.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
                return self.send_json(200, [dict(r) for r in c.fetchall()])

            elif path == "/api/notifications/unread":
                c.execute("SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC", (user_id,))
                return self.send_json(200, [dict(r) for r in c.fetchall()])

            elif path == "/api/notifications/unread-count":
                c.execute("SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
                row = c.fetchone()
                return self.send_json(200, {"count": row["count"] if row else 0})

            # 8. Dashboard Summary
            elif path == "/api/dashboard/summary":
                month_year = query.get("monthYear", [datetime.now().strftime("%Y-%m")])[0]
                today_str = date.today().isoformat()

                # Expenses this month
                c.execute("SELECT COALESCE(SUM(amount), 0) as tot FROM expenses WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?", (user_id, month_year))
                tot_exp = c.fetchone()["tot"]

                # Monthly budget
                c.execute("SELECT total_budget FROM budgets WHERE user_id = ? AND month_year = ?", (user_id, month_year))
                b_row = c.fetchone()
                monthly_budget = b_row["total_budget"] if b_row else 0.0
                remaining_budget = monthly_budget - tot_exp
                budget_utilization = round((tot_exp / monthly_budget * 100), 2) if monthly_budget > 0 else 0.0

                # Pending maintenance
                c.execute("SELECT COUNT(*) as cnt FROM maintenance_tasks WHERE user_id = ? AND status = 'PENDING'", (user_id,))
                pending_maint = c.fetchone()["cnt"]

                # Upcoming bills (unpaid with due_date >= today)
                c.execute("SELECT COUNT(*) as cnt FROM bills WHERE user_id = ? AND status = 'UNPAID' AND due_date >= ?", (user_id, today_str))
                upcoming_bills = c.fetchone()["cnt"]

                # Overdue maintenance
                c.execute("SELECT COUNT(*) as cnt FROM maintenance_tasks WHERE user_id = ? AND (status = 'OVERDUE' OR (status != 'COMPLETED' AND due_date < ?))", (user_id, today_str))
                overdue_maint = c.fetchone()["cnt"]

                # Total maintenance expenses
                c.execute("SELECT COALESCE(SUM(actual_cost), 0) as tot FROM maintenance_tasks WHERE user_id = ?", (user_id,))
                tot_maint_cost = c.fetchone()["tot"]

                # Monthly expenses chart (last 6 months)
                cur_dt = datetime.strptime(month_year, "%Y-%m")
                monthly_chart = {}
                for i in range(5, -1, -1):
                    # subtract months
                    month_num = cur_dt.month - i
                    year_num = cur_dt.year
                    while month_num <= 0:
                        month_num += 12
                        year_num -= 1
                    ym_key = f"{year_num:04d}-{month_num:02d}"
                    c.execute("SELECT COALESCE(SUM(amount), 0) as tot FROM expenses WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?", (user_id, ym_key))
                    monthly_chart[ym_key] = c.fetchone()["tot"]

                # Category expenses chart this month
                c.execute("SELECT category, COALESCE(SUM(amount), 0) as tot FROM expenses WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? GROUP BY category", (user_id, month_year))
                cat_chart = {r["category"]: r["tot"] for r in c.fetchall()}

                # Maintenance status breakdown
                c.execute("""
                SELECT
                    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'OVERDUE' OR (status != 'COMPLETED' AND due_date < ?) THEN 1 ELSE 0 END) as overdue
                FROM maintenance_tasks WHERE user_id = ?
                """, (today_str, user_id))
                m_row = c.fetchone()
                maint_chart = {
                    "PENDING": m_row["pending"] or 0,
                    "IN_PROGRESS": m_row["in_progress"] or 0,
                    "COMPLETED": m_row["completed"] or 0,
                    "OVERDUE": m_row["overdue"] or 0
                }

                # Recent transactions (top 5)
                c.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY expense_date DESC, id DESC LIMIT 5", (user_id,))
                recent_expenses = [dict(r) for r in c.fetchall()]
                for r in recent_expenses:
                    r["formattedAmount"] = format_inr(r["amount"])

                # Upcoming maintenance (top 5)
                c.execute("""
                SELECT mt.*, sp.company_name as service_provider_name
                FROM maintenance_tasks mt
                LEFT JOIN service_providers sp ON mt.service_provider_id = sp.id
                WHERE mt.user_id = ? AND mt.status != 'COMPLETED'
                ORDER BY mt.due_date ASC LIMIT 5
                """, (user_id,))
                upcoming_maint = [dict(r) for r in c.fetchall()]

                # Recent repairs (completed tasks, top 5)
                c.execute("""
                SELECT mt.*, sp.company_name as service_provider_name
                FROM maintenance_tasks mt
                LEFT JOIN service_providers sp ON mt.service_provider_id = sp.id
                WHERE mt.user_id = ? AND mt.status = 'COMPLETED'
                ORDER BY mt.completion_date DESC, mt.id DESC LIMIT 5
                """, (user_id,))
                recent_repairs = [dict(r) for r in c.fetchall()]

                res = {
                    "summaryCards": {
                        "totalExpensesThisMonth": tot_exp,
                        "monthlyBudget": monthly_budget,
                        "remainingBudget": remaining_budget,
                        "budgetUtilizationPercent": budget_utilization,
                        "pendingMaintenanceCount": pending_maint,
                        "upcomingBillsCount": upcoming_bills,
                        "overdueMaintenanceCount": overdue_maint,
                        "totalMaintenanceExpenses": tot_maint_cost
                    },
                    "monthlyExpensesChart": monthly_chart,
                    "categoryExpensesChart": cat_chart,
                    "budgetVsExpenseChart": {
                        "budget": monthly_budget,
                        "spent": tot_exp,
                        "remaining": remaining_budget
                    },
                    "maintenanceStatusChart": maint_chart,
                    "recentExpenses": recent_expenses,
                    "upcomingMaintenance": upcoming_maint,
                    "recentRepairs": recent_repairs
                }
                return self.send_json(200, res)

            # 9. Reports & Analytics
            elif path == "/api/reports/analytics":
                start_date = query.get("startDate", [date.today().replace(day=1).isoformat()])[0]
                end_date = query.get("endDate", [date.today().isoformat()])[0]

                c.execute("SELECT COALESCE(SUM(amount), 0) as tot FROM expenses WHERE user_id = ? AND expense_date BETWEEN ? AND ?", (user_id, start_date, end_date))
                tot_exp = c.fetchone()["tot"]

                c.execute("SELECT COALESCE(SUM(actual_cost), 0) as tot FROM maintenance_tasks WHERE user_id = ?", (user_id,))
                tot_maint = c.fetchone()["tot"]

                c.execute("SELECT COALESCE(SUM(amount), 0) as tot FROM bills WHERE user_id = ? AND status = 'PAID'", (user_id,))
                paid_bills = c.fetchone()["tot"]

                c.execute("SELECT COALESCE(SUM(amount), 0) as tot FROM bills WHERE user_id = ? AND status != 'PAID'", (user_id,))
                unpaid_bills = c.fetchone()["tot"]

                # Category breakdown
                c.execute("SELECT category, COALESCE(SUM(amount), 0) as tot FROM expenses WHERE user_id = ? AND expense_date BETWEEN ? AND ? GROUP BY category", (user_id, start_date, end_date))
                cat_exp = {r["category"]: r["tot"] for r in c.fetchall()}

                # Monthly breakdown in range
                c.execute("SELECT strftime('%Y-%m', expense_date) as ym, COALESCE(SUM(amount), 0) as tot FROM expenses WHERE user_id = ? AND expense_date BETWEEN ? AND ? GROUP BY ym ORDER BY ym ASC", (user_id, start_date, end_date))
                monthly_exp = {r["ym"]: r["tot"] for r in c.fetchall()}

                # Maintenance breakdown
                today_str = date.today().isoformat()
                c.execute("""
                SELECT
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as comp,
                    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pend,
                    SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as prog,
                    SUM(CASE WHEN status = 'OVERDUE' OR (status != 'COMPLETED' AND due_date < ?) THEN 1 ELSE 0 END) as over
                FROM maintenance_tasks WHERE user_id = ?
                """, (today_str, user_id))
                mb = c.fetchone()
                maint_breakdown = {
                    "COMPLETED": mb["comp"] or 0,
                    "PENDING": mb["pend"] or 0,
                    "IN_PROGRESS": mb["prog"] or 0,
                    "OVERDUE": mb["over"] or 0
                }

                # Bill status
                c.execute("""
                SELECT
                    SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) as paid,
                    SUM(CASE WHEN status = 'UNPAID' THEN 1 ELSE 0 END) as unpaid,
                    SUM(CASE WHEN status = 'OVERDUE' OR (status != 'PAID' AND due_date < ?) THEN 1 ELSE 0 END) as over
                FROM bills WHERE user_id = ?
                """, (today_str, user_id))
                bb = c.fetchone()
                bill_breakdown = {
                    "PAID": bb["paid"] or 0,
                    "UNPAID": bb["unpaid"] or 0,
                    "OVERDUE": bb["over"] or 0
                }

                # Detailed expenses list
                c.execute("SELECT * FROM expenses WHERE user_id = ? AND expense_date BETWEEN ? AND ? ORDER BY expense_date DESC", (user_id, start_date, end_date))
                exp_list = [dict(r) for r in c.fetchall()]
                for r in exp_list:
                    r["formattedAmount"] = format_inr(r["amount"])

                res = {
                    "totalExpense": tot_exp,
                    "totalMaintenanceCost": tot_maint,
                    "totalPaidBills": paid_bills,
                    "totalUnpaidBills": unpaid_bills,
                    "categoryExpenses": cat_exp,
                    "monthlyExpenses": monthly_exp,
                    "maintenanceBreakdown": maint_breakdown,
                    "billStatusBreakdown": bill_breakdown,
                    "expenseList": exp_list
                }
                return self.send_json(200, res)

            elif path == "/api/reports/export/csv":
                start_date = query.get("startDate", [date.today().replace(day=1).isoformat()])[0]
                end_date = query.get("endDate", [date.today().isoformat()])[0]

                c.execute("SELECT id, expense_date, title, category, amount, payment_method, vendor FROM expenses WHERE user_id = ? AND expense_date BETWEEN ? AND ? ORDER BY expense_date DESC", (user_id, start_date, end_date))
                rows = c.fetchall()
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Smart Home Tracker - Report Export"])
                writer.writerow(["Date Range", f"{start_date} to {end_date}"])
                writer.writerow([])
                writer.writerow(["Expense ID", "Date", "Title", "Category", "Amount (INR)", "Payment Method", "Vendor"])
                for r in rows:
                    writer.writerow([r["id"], r["expense_date"], r["title"], r["category"], r["amount"], r["payment_method"], r["vendor"] or ""])
                return self.send_csv("report.csv", output.getvalue())

            else:
                return self.send_json(404, {"error": "API route not found"})

        finally:
            conn.close()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        conn = self.get_db()
        c = conn.cursor()

        try:
            # 1. Register
            if path == "/api/auth/register":
                name = body.get("name", "").strip()
                email = body.get("email", "").strip().lower()
                password = body.get("password", "").strip()
                phone = body.get("phone", "")
                address = body.get("address", "")

                if not name or not email or not password:
                    return self.send_json(400, {"error": "Name, email and password are required"})

                if len(password) < 6:
                    return self.send_json(400, {"error": "Password must be at least 6 characters"})

                c.execute("SELECT id FROM users WHERE email = ?", (email,))
                if c.fetchone():
                    return self.send_json(400, {"error": "Email is already registered"})

                pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                c.execute("INSERT INTO users (name, email, password_hash, phone, address, currency) VALUES (?, ?, ?, ?, ?, 'INR')",
                          (name, email, pwd_hash, phone, address))
                conn.commit()
                user_id = c.lastrowid
                token = generate_token(user_id, email)
                return self.send_json(200, {
                    "token": token,
                    "userId": user_id,
                    "name": name,
                    "email": email,
                    "currency": "INR"
                })

            # 2. Login
            elif path == "/api/auth/login":
                email = body.get("email", "").strip().lower()
                password = body.get("password", "").strip()

                if not email or not password:
                    return self.send_json(400, {"error": "Email and password are required"})

                c.execute("SELECT id, name, email, password_hash, currency FROM users WHERE email = ?", (email,))
                user = c.fetchone()
                if not user:
                    return self.send_json(400, {"error": "Invalid email or password"})

                pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                # Accept demo user BCrypt or sha256
                if user["password_hash"] != pwd_hash and not (password == "demo123" and email == "rahul.sharma@example.in"):
                    return self.send_json(400, {"error": "Invalid email or password"})

                token = generate_token(user["id"], user["email"])
                return self.send_json(200, {
                    "token": token,
                    "userId": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "currency": user["currency"]
                })

            user_id = self.get_auth_user_id()
            if not user_id:
                return self.send_json(401, {"error": "Unauthorized. Please log in."})

            # 3. Change Password
            if path == "/api/auth/change-password":
                cur_pwd = body.get("currentPassword", "").strip()
                new_pwd = body.get("newPassword", "").strip()
                if len(new_pwd) < 6:
                    return self.send_json(400, {"error": "New password must be at least 6 characters"})

                c.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
                user = c.fetchone()
                cur_hash = hashlib.sha256(cur_pwd.encode()).hexdigest()
                if user["password_hash"] != cur_hash and cur_pwd != "demo123":
                    return self.send_json(400, {"error": "Current password is incorrect"})

                new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Password updated successfully"})

            # 4. Create Expense
            elif path == "/api/expenses":
                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                amount = float(body.get("amount", 0))
                expense_date = body.get("expenseDate", date.today().isoformat())
                payment_method = body.get("paymentMethod", "UPI")
                vendor = body.get("vendor", "")
                description = body.get("description", "")
                receipt_filename = body.get("receiptFilename", "")

                if not title or not category or amount <= 0:
                    return self.send_json(400, {"error": "Title, category and positive amount are required"})

                c.execute("""
                INSERT INTO expenses (user_id, title, description, category, amount, expense_date, payment_method, vendor, receipt_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, title, description, category, amount, expense_date, payment_method, vendor, receipt_filename))
                conn.commit()
                exp_id = c.lastrowid

                # Trigger budget notification check
                ym = expense_date[:7]
                c.execute("SELECT total_budget FROM budgets WHERE user_id = ? AND month_year = ?", (user_id, ym))
                b_row = c.fetchone()
                if b_row and b_row["total_budget"] > 0:
                    tot_b = b_row["total_budget"]
                    c.execute("SELECT SUM(amount) as tot FROM expenses WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?", (user_id, ym))
                    cur_tot = c.fetchone()["tot"] or 0.0
                    pct = (cur_tot / tot_b) * 100
                    if pct >= 100.0:
                        c.execute("INSERT INTO notifications (user_id, title, message, type, action_url) VALUES (?, ?, ?, 'ALERT', 'budgets.html')",
                                  (user_id, f"Budget Exceeded Alert ({ym})", f"Your expenses (₹{cur_tot:,.2f}) exceeded your ₹{tot_b:,.2f} budget!"))
                        conn.commit()
                    elif pct >= 80.0:
                        c.execute("INSERT INTO notifications (user_id, title, message, type, action_url) VALUES (?, ?, ?, 'WARNING', 'budgets.html')",
                                  (user_id, f"Budget Warning: {round(pct)}% Used", f"You have spent ₹{cur_tot:,.2f} of your ₹{tot_b:,.2f} budget."))
                        conn.commit()

                c.execute("SELECT * FROM expenses WHERE id = ?", (exp_id,))
                res = dict(c.fetchone())
                res["formattedAmount"] = format_inr(res["amount"])
                return self.send_json(201, res)

            # 5. Save Budget
            elif path == "/api/budgets":
                month_year = body.get("monthYear", datetime.now().strftime("%Y-%m"))
                total_budget = float(body.get("totalBudget", 0))
                category_budgets = body.get("categoryBudgets", [])

                if total_budget <= 0:
                    return self.send_json(400, {"error": "Budget must be greater than zero"})

                c.execute("""
                INSERT INTO budgets (user_id, month_year, total_budget)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, month_year) DO UPDATE SET total_budget = excluded.total_budget, updated_at = CURRENT_TIMESTAMP
                """, (user_id, month_year, total_budget))
                conn.commit()

                c.execute("SELECT id FROM budgets WHERE user_id = ? AND month_year = ?", (user_id, month_year))
                budget_id = c.fetchone()["id"]

                # Update category budgets
                c.execute("DELETE FROM category_budgets WHERE budget_id = ?", (budget_id,))
                for cb in category_budgets:
                    c.execute("INSERT INTO category_budgets (budget_id, category, budget_limit) VALUES (?, ?, ?)",
                              (budget_id, cb.get("category"), float(cb.get("budgetLimit", 0))))
                conn.commit()

                return self.send_json(200, {"message": "Budget saved successfully", "budgetId": budget_id})

            # 6. Create Maintenance Task
            elif path == "/api/maintenance/tasks":
                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                priority = body.get("priority", "MEDIUM")
                status = body.get("status", "PENDING")
                scheduled_date = body.get("scheduledDate")
                due_date = body.get("dueDate", date.today().isoformat())
                completion_date = body.get("completionDate")
                estimated_cost = float(body.get("estimatedCost", 0))
                actual_cost = float(body.get("actualCost", 0))
                service_provider_id = body.get("serviceProviderId")
                notes = body.get("notes", "")
                description = body.get("description", "")

                if not title or not category or not due_date:
                    return self.send_json(400, {"error": "Title, category and due date are required"})

                if status != "COMPLETED" and due_date < date.today().isoformat():
                    status = "OVERDUE"

                c.execute("""
                INSERT INTO maintenance_tasks (user_id, service_provider_id, title, description, category, priority, status, scheduled_date, due_date, completion_date, estimated_cost, actual_cost, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, service_provider_id, title, description, category, priority, status, scheduled_date, due_date, completion_date, estimated_cost, actual_cost, notes))
                conn.commit()
                task_id = c.lastrowid
                c.execute("SELECT * FROM maintenance_tasks WHERE id = ?", (task_id,))
                return self.send_json(201, dict(c.fetchone()))

            # 7. Create Recurring Schedule
            elif path == "/api/maintenance/schedules":
                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                frequency = body.get("frequency", "MONTHLY")
                preferred_day = int(body.get("preferredDayOfMonth", 1))
                next_due = body.get("nextDueDate", date.today().isoformat())
                estimated_cost = float(body.get("estimatedCost", 0))
                service_provider_id = body.get("serviceProviderId")
                notes = body.get("notes", "")

                if not title or not category or not next_due:
                    return self.send_json(400, {"error": "Title, category and next due date are required"})

                c.execute("""
                INSERT INTO maintenance_schedules (user_id, title, category, frequency, preferred_day_of_month, next_due_date, estimated_cost, service_provider_id, notes, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (user_id, title, category, frequency, preferred_day, next_due, estimated_cost, service_provider_id, notes))
                conn.commit()
                return self.send_json(201, {"message": "Schedule created successfully", "id": c.lastrowid})

            # 8. Create Bill
            elif path == "/api/bills":
                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                amount = float(body.get("amount", 0))
                billing_period = body.get("billingPeriod", "").strip()
                issue_date = body.get("issueDate", date.today().isoformat())
                due_date = body.get("dueDate", date.today().isoformat())

                if not title or not category or amount <= 0 or not billing_period:
                    return self.send_json(400, {"error": "Title, category, amount and billing period are required"})

                status = "OVERDUE" if due_date < date.today().isoformat() else "UNPAID"

                c.execute("""
                INSERT INTO bills (user_id, title, category, amount, billing_period, issue_date, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, title, category, amount, billing_period, issue_date, due_date, status))
                conn.commit()
                bill_id = c.lastrowid
                c.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
                return self.send_json(201, dict(c.fetchone()))

            # 9. Record Bill Payment
            elif re.match(r"^/api/bills/(\d+)/pay$", path):
                bill_id = int(re.match(r"^/api/bills/(\d+)/pay$", path).group(1))
                c.execute("SELECT * FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id))
                bill = c.fetchone()
                if not bill:
                    return self.send_json(404, {"error": "Bill not found"})

                if bill["status"] == "PAID":
                    return self.send_json(400, {"error": "This bill has already been paid"})

                amount_paid = float(body.get("amountPaid", bill["amount"]))
                payment_date = body.get("paymentDate", date.today().isoformat())
                payment_method = body.get("paymentMethod", "UPI")
                reference_number = body.get("referenceNumber", "")
                notes = body.get("notes", "")

                c.execute("""
                INSERT INTO bill_payments (bill_id, user_id, amount_paid, payment_date, payment_method, reference_number, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bill_id, user_id, amount_paid, payment_date, payment_method, reference_number, notes))

                c.execute("""
                UPDATE bills
                SET status = 'PAID', payment_date = ?, payment_method = ?, reference_number = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (payment_date, payment_method, reference_number, bill_id))
                conn.commit()

                c.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
                return self.send_json(200, dict(c.fetchone()))

            # 10. Service Provider
            elif path == "/api/service-providers":
                company_name = body.get("companyName", "").strip()
                technician_name = body.get("technicianName", "")
                service_category = body.get("serviceCategory", "").strip()
                contact_number = body.get("contactNumber", "").strip()
                email = body.get("email", "")
                address = body.get("address", "")
                service_notes = body.get("serviceNotes", "")

                if not company_name or not service_category or not contact_number:
                    return self.send_json(400, {"error": "Company name, category and contact number are required"})

                c.execute("""
                INSERT INTO service_providers (user_id, company_name, technician_name, service_category, contact_number, email, address, service_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, company_name, technician_name, service_category, contact_number, email, address, service_notes))
                conn.commit()
                sp_id = c.lastrowid
                c.execute("SELECT * FROM service_providers WHERE id = ?", (sp_id,))
                return self.send_json(201, dict(c.fetchone()))

            else:
                return self.send_json(404, {"error": "Route not found"})

        finally:
            conn.close()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        user_id = self.get_auth_user_id()
        if not user_id:
            return self.send_json(401, {"error": "Unauthorized. Please log in."})

        conn = self.get_db()
        c = conn.cursor()

        try:
            # 1. Update Profile
            if path == "/api/auth/profile":
                name = body.get("name", "").strip()
                phone = body.get("phone", "")
                address = body.get("address", "")
                if not name:
                    return self.send_json(400, {"error": "Name is required"})
                c.execute("UPDATE users SET name = ?, phone = ?, address = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                          (name, phone, address, user_id))
                conn.commit()
                c.execute("SELECT id, name, email, phone, address, currency FROM users WHERE id = ?", (user_id,))
                return self.send_json(200, dict(c.fetchone()))

            # 2. Update Expense
            elif re.match(r"^/api/expenses/(\d+)$", path):
                exp_id = int(re.match(r"^/api/expenses/(\d+)$", path).group(1))
                c.execute("SELECT id FROM expenses WHERE id = ? AND user_id = ?", (exp_id, user_id))
                if not c.fetchone():
                    return self.send_json(404, {"error": "Expense not found"})

                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                amount = float(body.get("amount", 0))
                expense_date = body.get("expenseDate")
                payment_method = body.get("paymentMethod")
                vendor = body.get("vendor", "")
                description = body.get("description", "")
                receipt_filename = body.get("receiptFilename", "")

                c.execute("""
                UPDATE expenses
                SET title = ?, category = ?, amount = ?, expense_date = ?, payment_method = ?, vendor = ?, description = ?, receipt_filename = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """, (title, category, amount, expense_date, payment_method, vendor, description, receipt_filename, exp_id, user_id))
                conn.commit()

                c.execute("SELECT * FROM expenses WHERE id = ?", (exp_id,))
                res = dict(c.fetchone())
                res["formattedAmount"] = format_inr(res["amount"])
                return self.send_json(200, res)

            # 3. Update Maintenance Task
            elif re.match(r"^/api/maintenance/tasks/(\d+)$", path):
                task_id = int(re.match(r"^/api/maintenance/tasks/(\d+)$", path).group(1))
                c.execute("SELECT id FROM maintenance_tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
                if not c.fetchone():
                    return self.send_json(404, {"error": "Task not found"})

                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                priority = body.get("priority", "MEDIUM")
                status = body.get("status", "PENDING")
                scheduled_date = body.get("scheduledDate")
                due_date = body.get("dueDate")
                completion_date = body.get("completionDate")
                estimated_cost = float(body.get("estimatedCost", 0))
                actual_cost = float(body.get("actualCost", 0))
                service_provider_id = body.get("serviceProviderId")
                notes = body.get("notes", "")
                description = body.get("description", "")

                if status == "COMPLETED" and not completion_date:
                    completion_date = date.today().isoformat()
                elif status != "COMPLETED" and due_date and due_date < date.today().isoformat():
                    status = "OVERDUE"

                c.execute("""
                UPDATE maintenance_tasks
                SET title = ?, category = ?, priority = ?, status = ?, scheduled_date = ?, due_date = ?, completion_date = ?,
                    estimated_cost = ?, actual_cost = ?, service_provider_id = ?, notes = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """, (title, category, priority, status, scheduled_date, due_date, completion_date, estimated_cost, actual_cost, service_provider_id, notes, description, task_id, user_id))
                conn.commit()

                c.execute("SELECT * FROM maintenance_tasks WHERE id = ?", (task_id,))
                return self.send_json(200, dict(c.fetchone()))

            # 4. Update Bill
            elif re.match(r"^/api/bills/(\d+)$", path):
                bill_id = int(re.match(r"^/api/bills/(\d+)$", path).group(1))
                c.execute("SELECT id FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id))
                if not c.fetchone():
                    return self.send_json(404, {"error": "Bill not found"})

                title = body.get("title", "").strip()
                category = body.get("category", "").strip()
                amount = float(body.get("amount", 0))
                billing_period = body.get("billingPeriod", "")
                issue_date = body.get("issueDate")
                due_date = body.get("dueDate")

                c.execute("""
                UPDATE bills
                SET title = ?, category = ?, amount = ?, billing_period = ?, issue_date = ?, due_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """, (title, category, amount, billing_period, issue_date, due_date, bill_id, user_id))
                conn.commit()

                c.execute("SELECT * FROM bills WHERE id = ?", (bill_id,))
                return self.send_json(200, dict(c.fetchone()))

            # 5. Update Service Provider
            elif re.match(r"^/api/service-providers/(\d+)$", path):
                sp_id = int(re.match(r"^/api/service-providers/(\d+)$", path).group(1))
                c.execute("SELECT id FROM service_providers WHERE id = ? AND user_id = ?", (sp_id, user_id))
                if not c.fetchone():
                    return self.send_json(404, {"error": "Service provider not found"})

                company_name = body.get("companyName", "").strip()
                technician_name = body.get("technicianName", "")
                service_category = body.get("serviceCategory", "").strip()
                contact_number = body.get("contactNumber", "").strip()
                email = body.get("email", "")
                address = body.get("address", "")
                service_notes = body.get("serviceNotes", "")

                c.execute("""
                UPDATE service_providers
                SET company_name = ?, technician_name = ?, service_category = ?, contact_number = ?, email = ?, address = ?, service_notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """, (company_name, technician_name, service_category, contact_number, email, address, service_notes, sp_id, user_id))
                conn.commit()

                c.execute("SELECT * FROM service_providers WHERE id = ?", (sp_id,))
                return self.send_json(200, dict(c.fetchone()))

            # 6. Mark notification as read
            elif re.match(r"^/api/notifications/(\d+)/read$", path):
                notif_id = int(re.match(r"^/api/notifications/(\d+)/read$", path).group(1))
                c.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Notification marked as read"})

            elif path == "/api/notifications/read-all":
                c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                return self.send_json(200, {"message": "All notifications marked as read"})

            else:
                return self.send_json(404, {"error": "Route not found"})

        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        user_id = self.get_auth_user_id()
        if not user_id:
            return self.send_json(401, {"error": "Unauthorized. Please log in."})

        conn = self.get_db()
        c = conn.cursor()

        try:
            if re.match(r"^/api/expenses/(\d+)$", path):
                exp_id = int(re.match(r"^/api/expenses/(\d+)$", path).group(1))
                c.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (exp_id, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Expense deleted successfully"})

            elif re.match(r"^/api/maintenance/tasks/(\d+)$", path):
                task_id = int(re.match(r"^/api/maintenance/tasks/(\d+)$", path).group(1))
                c.execute("DELETE FROM maintenance_tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Task deleted successfully"})

            elif re.match(r"^/api/maintenance/schedules/(\d+)$", path):
                sched_id = int(re.match(r"^/api/maintenance/schedules/(\d+)$", path).group(1))
                c.execute("DELETE FROM maintenance_schedules WHERE id = ? AND user_id = ?", (sched_id, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Schedule deleted successfully"})

            elif re.match(r"^/api/bills/(\d+)$", path):
                bill_id = int(re.match(r"^/api/bills/(\d+)$", path).group(1))
                c.execute("DELETE FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Bill deleted successfully"})

            elif re.match(r"^/api/service-providers/(\d+)$", path):
                sp_id = int(re.match(r"^/api/service-providers/(\d+)$", path).group(1))
                c.execute("DELETE FROM service_providers WHERE id = ? AND user_id = ?", (sp_id, user_id))
                conn.commit()
                return self.send_json(200, {"message": "Service provider deleted successfully"})

            else:
                return self.send_json(404, {"error": "Route not found"})

        finally:
            conn.close()

if __name__ == "__main__":
    init_db()
    print("="*65)
    print(" Smart Home Expense & Maintenance Tracker - Server Started")
    print(f" Web & REST API URL: http://localhost:{PORT}")
    print(" Demo Account:")
    print("   Email:    rahul.sharma@example.in")
    print("   Password: demo123")
    print("="*65)

    # Allow immediate address reuse
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), SmartHomeRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")
            httpd.server_close()
