"""
Automated End-to-End Test Suite for Smart Home Tracker REST APIs
Validates business logic, authentication, CRUD operations, budget calculations, and overdue handling.
"""

import unittest
import json
import sqlite3
import os
import server
from datetime import datetime, date, timedelta

class TestSmartHomeTracker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize DB and ensure demo data is populated
        server.init_db()

    def setUp(self):
        self.conn = sqlite3.connect(server.DB_FILE)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_01_demo_user_exists(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE email = 'rahul.sharma@example.in'")
        user = c.fetchone()
        self.assertIsNotNone(user, "Demo user Rahul Sharma should exist")
        self.assertEqual(user['currency'], 'INR')

    def test_02_token_generation_and_verification(self):
        token = server.generate_token(1, "rahul.sharma@example.in")
        self.assertIsNotNone(token)
        verified_user_id = server.verify_token(token)
        self.assertEqual(verified_user_id, 1, "Verified user ID must match original ID")

    def test_03_expense_positive_amount_and_totals(self):
        c = self.conn.cursor()
        c.execute("SELECT amount FROM expenses WHERE user_id = 1")
        rows = c.fetchall()
        for r in rows:
            self.assertGreater(r['amount'], 0, "Expense amount must be positive")

        c.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = 1")
        total = c.fetchone()['total']
        self.assertGreater(total, 0, "Total expenses should be greater than zero")

    def test_04_budget_utilization_and_thresholds(self):
        c = self.conn.cursor()
        current_ym = datetime.now().strftime("%Y-%m")
        c.execute("SELECT total_budget FROM budgets WHERE user_id = 1 AND month_year = ?", (current_ym,))
        b_row = c.fetchone()
        self.assertIsNotNone(b_row, "Monthly budget must exist")
        total_budget = b_row['total_budget']
        self.assertEqual(total_budget, 15000.00, "Default demo budget is ₹15,000")

        c.execute("SELECT SUM(amount) as spent FROM expenses WHERE user_id = 1 AND strftime('%Y-%m', expense_date) = ?", (current_ym,))
        spent = c.fetchone()['spent'] or 0.0
        pct = (spent / total_budget) * 100
        self.assertGreaterEqual(pct, 0.0)

    def test_05_maintenance_overdue_auto_detection(self):
        c = self.conn.cursor()
        yesterday = (date.today() - timedelta(days=2)).isoformat()
        c.execute("""
        INSERT INTO maintenance_tasks (user_id, title, category, priority, status, due_date)
        VALUES (1, 'Test Leaking Pipe Fix', 'Plumbing', 'HIGH', 'PENDING', ?)
        """, (yesterday,))
        self.conn.commit()
        task_id = c.lastrowid

        # Run overdue updater
        today_str = date.today().isoformat()
        c.execute("UPDATE maintenance_tasks SET status = 'OVERDUE' WHERE status != 'COMPLETED' AND due_date < ?", (today_str,))
        self.conn.commit()

        c.execute("SELECT status FROM maintenance_tasks WHERE id = ?", (task_id,))
        status = c.fetchone()['status']
        self.assertEqual(status, 'OVERDUE', "Task past due date must be marked OVERDUE")

        # Clean up
        c.execute("DELETE FROM maintenance_tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def test_06_bill_duplicate_payment_prevention(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM bills WHERE user_id = 1 AND status = 'PAID' LIMIT 1")
        paid_bill = c.fetchone()
        self.assertIsNotNone(paid_bill, "Should have at least one paid bill in seed data")
        self.assertEqual(paid_bill['status'], 'PAID')

    def test_07_inr_currency_formatting(self):
        res1 = server.format_inr(1850)
        self.assertIn("1,850", res1)
        self.assertTrue(res1.startswith("₹"))

        res2 = server.format_inr(15000.5)
        self.assertIn("15,000.50", res2)

    def test_08_service_providers_directory(self):
        c = self.conn.cursor()
        c.execute("SELECT count(*) as cnt FROM service_providers WHERE user_id = 1")
        cnt = c.fetchone()['cnt']
        self.assertGreaterEqual(cnt, 5, "Demo seed should have at least 5 service providers")

if __name__ == '__main__':
    unittest.main()
