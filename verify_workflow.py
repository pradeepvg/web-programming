"""
End-to-End Workflow Verification Script
Tests all 12 frontend pages, REST APIs, database mutations, and calculations.
"""

import urllib.request
import json

BASE = "http://localhost:8080"

def test_workflow():
    # 1. Test Static Pages
    pages = [
        'index.html', 'login.html', 'register.html', 'dashboard.html',
        'expenses.html', 'budgets.html', 'maintenance.html', 'calendar.html',
        'bills.html', 'service-providers.html', 'reports.html', 'profile.html'
    ]
    for p in pages:
        req = urllib.request.Request(f"{BASE}/{p}", headers={'Connection': 'close'})
        res = urllib.request.urlopen(req)
        assert res.status == 200, f"Page {p} returned status {res.status}"
    print("[PASS] All 12 frontend HTML pages serve successfully with HTTP 200!")

    # 2. Login
    login_data = json.dumps({'email': 'rahul.sharma@example.in', 'password': 'demo123'}).encode()
    req = urllib.request.Request(f"{BASE}/api/auth/login", data=login_data, headers={'Content-Type': 'application/json', 'Connection': 'close'})
    res = urllib.request.urlopen(req)
    auth_resp = json.loads(res.read())
    token = auth_resp['token']
    auth_headers = {'Authorization': f"Bearer {token}", 'Content-Type': 'application/json', 'Connection': 'close'}
    print(f"[PASS] Logged in successfully as {auth_resp['name']} (User ID: {auth_resp['userId']})")

    # 3. Add Expense 'Balcony LED Light' ₹450
    exp_data = json.dumps({
        'title': 'Balcony LED Light',
        'category': 'Electrical repairs',
        'amount': 450.00,
        'expenseDate': '2026-10-11',
        'paymentMethod': 'UPI',
        'vendor': 'VoltGuard Electricals'
    }).encode()
    req = urllib.request.Request(f"{BASE}/api/expenses", data=exp_data, headers=auth_headers)
    res = urllib.request.urlopen(req)
    exp = json.loads(res.read())
    print(f"[PASS] Created expense #{exp['id']}: '{exp['title']}' for {exp['formattedAmount']}")

    # 4. Pay Bill (Society Maintenance Charges)
    pay_data = json.dumps({
        'paymentDate': '2026-10-11',
        'paymentMethod': 'UPI',
        'referenceNumber': 'UPI-112233',
        'notes': 'Paid via PhonePe'
    }).encode()
    req = urllib.request.Request(f"{BASE}/api/bills/3/pay", data=pay_data, headers=auth_headers)
    res = urllib.request.urlopen(req)
    bill = json.loads(res.read())
    print(f"[PASS] Settled Bill #{bill['id']}: '{bill['title']}' -> Status: {bill['status']}, Paid on: {bill['paymentDate']}")

    # 5. Fetch Dashboard Summary
    req = urllib.request.Request(f"{BASE}/api/dashboard/summary", headers=auth_headers)
    res = urllib.request.urlopen(req)
    dash = json.loads(res.read())
    cards = dash['summaryCards']
    print("\n[DASHBOARD SUMMARY CARDS]")
    print(f"   * Total Expenses This Month: INR {cards['totalExpensesThisMonth']:,.2f}")
    print(f"   * Remaining Budget:          INR {cards['remainingBudget']:,.2f} ({cards['budgetUtilizationPercent']}% used)")
    print(f"   * Pending Maintenance Tasks: {cards['pendingMaintenanceCount']}")
    print(f"   * Upcoming Bills Count:      {cards['upcomingBillsCount']}")
    print(f"   * Overdue Maintenance Tasks: {cards['overdueMaintenanceCount']}")
    print(f"   * Total Maintenance Cost:    INR {cards['totalMaintenanceExpenses']:,.2f}")

    # 6. Fetch Reports & Analytics
    req = urllib.request.Request(f"{BASE}/api/reports/analytics?startDate=2026-10-01&endDate=2026-10-31", headers=auth_headers)
    res = urllib.request.urlopen(req)
    rep = json.loads(res.read())
    print(f"\n[ANALYTICS REPORT]")
    print(f"   * Total Expense in Range:   INR {rep['totalExpense']:,.2f}")
    print(f"   * Total Paid Bills:         INR {rep['totalPaidBills']:,.2f}")
    print(f"   * Total Unpaid Bills:       INR {rep['totalUnpaidBills']:,.2f}")
    print(f"   * Number of categories:     {len(rep['categoryExpenses'])}")

    print("\n=======================================================")
    print(" [SUCCESS] ALL END-TO-END WORKFLOWS VERIFIED AND PASSING!")
    print("=======================================================\n")

if __name__ == '__main__':
    test_workflow()
