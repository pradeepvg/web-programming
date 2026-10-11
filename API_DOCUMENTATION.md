# Smart Home Expense & Maintenance Tracker - REST API Documentation

Base URL: `http://localhost:8080/api`

All financial values are denominated and formatted in **Indian Rupees (₹ INR)**.
Protected endpoints require the HTTP Header:
```http
Authorization: Bearer <jwt_token>
```

---

## 1. Authentication Endpoints (`/api/auth`)

### `POST /api/auth/register`
Registers a new household account with BCrypt password encryption.

**Request Body:**
```json
{
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.in",
  "password": "demo123",
  "phone": "+91 98765 43210",
  "address": "Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "userId": 1,
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.in",
  "currency": "INR"
}
```

---

### `POST /api/auth/login`
Authenticates user credentials.

**Request Body:**
```json
{
  "email": "rahul.sharma@example.in",
  "password": "demo123"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "userId": 1,
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.in",
  "currency": "INR"
}
```

---

### `GET /api/auth/profile`
Retrieves current authenticated user's profile details.

---

### `PUT /api/auth/profile`
Updates contact information and home address.

---

### `POST /api/auth/change-password`
Changes account password verifying the previous password with BCrypt.

---

## 2. Dashboard Endpoints (`/api/dashboard`)

### `GET /api/dashboard/summary?monthYear=2026-10`
Returns dynamically calculated dashboard metrics, 4 Chart.js datasets, and 3 activity feeds.

**Response (200 OK):**
```json
{
  "summaryCards": {
    "totalExpensesThisMonth": 11119.00,
    "monthlyBudget": 15000.00,
    "remainingBudget": 3881.00,
    "budgetUtilizationPercent": 74.13,
    "pendingMaintenanceCount": 2,
    "upcomingBillsCount": 2,
    "overdueMaintenanceCount": 1,
    "totalMaintenanceExpenses": 1400.00
  },
  "monthlyExpensesChart": {
    "2026-05": 9400.00,
    "2026-06": 12850.00,
    "2026-07": 10200.00,
    "2026-08": 14100.00,
    "2026-09": 13450.00,
    "2026-10": 11119.00
  },
  "categoryExpensesChart": {
    "Electricity": 1850.00,
    "Water": 650.00,
    "Plumbing": 1200.00,
    "Internet": 999.00,
    "Groceries": 3450.00,
    "Gas": 850.00,
    "Air conditioning": 1500.00,
    "Electrical repairs": 620.00
  },
  "budgetVsExpenseChart": {
    "budget": 15000.00,
    "spent": 11119.00,
    "remaining": 3881.00
  },
  "maintenanceStatusChart": {
    "PENDING": 2,
    "IN_PROGRESS": 1,
    "COMPLETED": 1,
    "OVERDUE": 1
  },
  "recentExpenses": [...],
  "upcomingMaintenance": [...],
  "recentRepairs": [...]
}
```

---

## 3. Expenses Endpoints (`/api/expenses`)

- `GET /api/expenses`: Query parameters `category`, `paymentMethod`, `startDate`, `endDate`, `search`.
- `POST /api/expenses`: Create new expense record (validates positive amount & valid date).
- `PUT /api/expenses/{id}`: Update expense record.
- `DELETE /api/expenses/{id}`: Remove expense record.
- `GET /api/expenses/export/csv`: Downloads complete expense register as a CSV file.

---

## 4. Budgets Endpoints (`/api/budgets`)

- `GET /api/budgets?monthYear=2026-10`: Calculates dynamic spending, remaining balance, 80% warning flag, and 100% breach alert.
- `POST /api/budgets`: Sets monthly household budget and category allocations.

---

## 5. Maintenance Endpoints (`/api/maintenance`)

- `GET /api/maintenance/tasks`: Retrieves all maintenance tasks (calculates overdue status automatically if due date is in the past).
- `POST /api/maintenance/tasks`: Logs new maintenance task with priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`) and costs in ₹ INR.
- `PUT /api/maintenance/tasks/{id}`: Updates task details or marks as completed.
- `DELETE /api/maintenance/tasks/{id}`: Removes task.
- `GET /api/maintenance/schedules`: Lists recurring schedules (Monthly, Quarterly, Half-Yearly, Annual).
- `POST /api/maintenance/schedules`: Configures recurring schedule routine.
- `DELETE /api/maintenance/schedules/{id}`: Deletes schedule.

---

## 6. Household Bills Endpoints (`/api/bills`)

- `GET /api/bills?status=UNPAID`: Lists bills filtered by payment status (`UNPAID`, `PAID`, `OVERDUE`).
- `POST /api/bills`: Adds new utility bill statement.
- `PUT /api/bills/{id}`: Updates bill terms.
- `DELETE /api/bills/{id}`: Deletes bill record.
- `POST /api/bills/{id}/pay`: Records settlement transaction with duplicate protection, sets bill status to `PAID`, and logs payment metadata.

---

## 7. Service Providers Endpoints (`/api/service-providers`)

- `GET /api/service-providers`: Lists verified technicians.
- `POST /api/service-providers`: Registers technician or repair agency.
- `PUT /api/service-providers/{id}`: Updates contact information.
- `DELETE /api/service-providers/{id}`: Deletes provider.

---

## 8. Reports & Analytics (`/api/reports`)

- `GET /api/reports/analytics?startDate=...&endDate=...`: Returns comprehensive living expenses audit, maintenance costs, and settlement statistics.
- `GET /api/reports/export/csv`: Exports date-range report in CSV format.
