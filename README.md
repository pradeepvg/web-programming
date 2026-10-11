# Smart Home Expense & Maintenance Tracker 🏡

A modern, responsive, full-stack web application designed for comprehensive household financial accounting, preventive home maintenance, and utility billing management. Built with **Indian Rupees (₹ INR)** formatting, automated overdue detection, recurring maintenance schedules, and budget utilization thresholds.

---

## 🌟 Key Features

1. **Indian Rupee (₹ INR) Formatting**: Every financial figure follows Indian number notation (e.g., BESCOM Electricity: ₹1,850, Monthly Maintenance Budget: ₹15,000, AC Deep Cleaning: ₹1,500).
2. **Dynamic Master Dashboard**:
   - 6 Live Summary Cards: Month's Expenses, Remaining Budget, Pending Maintenance Tasks, Upcoming Utility Bills, Overdue Maintenance Alerts, and Total Repair Costs.
   - 4 Interactive Visualizations: Monthly expense trends bar chart, category doughnut chart, budget utilization health bar, and maintenance status breakdown.
   - Live Activity Feeds: Recent transactions, upcoming scheduled maintenance, and recent repair history.
3. **Expense Management**:
   - Complete CRUD operations with positive amount validation.
   - Multi-criteria filtering by category, payment method (UPI, Net Banking, Credit/Debit Card, Cash), and custom date ranges.
   - Search by keyword and vendor.
   - 1-Click CSV export of expense statements.
4. **Monthly Budget Planning**:
   - Household spending cap and category-specific allocations.
   - Automatic **80% Warning Banner** when spending approaches threshold.
   - Automatic **100%+ Danger Alert** when the budget ceiling is breached.
5. **Home Maintenance Management**:
   - Full task lifecycle: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `OVERDUE`.
   - Priority levels: `LOW`, `MEDIUM`, `HIGH`, `URGENT`.
   - Automated overdue detection when the due date passes without completion.
   - Estimated vs. actual cost tracking in ₹ INR.
6. **Maintenance Scheduler & Calendar**:
   - Monthly calendar view showing due-today tasks, scheduled servicing, and overdue alerts.
   - Automated recurring cycles: Monthly (Water purifier RO check), Quarterly (AC chemical wash), Half-Yearly (Electrical & inverter batteries), and Annual (Terrace waterproofing & painting).
7. **Household Bills Management**:
   - Track utility bills with billing periods and due dates.
   - Record payment modal with duplicate payment prevention and transaction/UTR reference numbers.
   - Status tracking: `UNPAID`, `PAID`, `OVERDUE`.
8. **Service Provider Directory**:
   - Directory of verified technicians and service agencies (plumbers, electricians, AC care).
   - Direct click-to-call links and service specialty notes.
9. **Reports & Analytics**:
   - Interactive date-range analytics.
   - Visual breakdown of living costs and bill settlement rates.
   - 1-Click Comprehensive Report CSV export.
10. **Authentication & Security**:
    - BCrypt password hashing.
    - Stateless JWT token authorization.
    - Light / Dark theme toggle with persistent state.

---

## 📂 Project Architecture

```
Web programming/
├── pom.xml                                   # Maven configuration for Spring Boot 3.3.4
├── schema.sql                                # MySQL relational database schema
├── data.sql                                  # Realistic Indian household seed data in ₹ INR
├── server.py                                 # Local runnable REST server (Python 3.14 + SQLite)
├── test_app.py                               # Automated REST API & business logic test suite
├── API_DOCUMENTATION.md                      # Complete REST API specifications
├── README.md                                 # Project documentation
│
├── src/                                      # Enterprise Spring Boot Backend
│   ├── main/
│   │   ├── java/com/smarthome/tracker/
│   │   │   ├── SmartHomeTrackerApplication.java
│   │   │   ├── config/                       # WebMvc & Security configs
│   │   │   ├── controller/                   # Spring MVC REST Controllers
│   │   │   ├── dto/                          # Request & Response DTOs
│   │   │   ├── entity/                       # JPA Relational Entities
│   │   │   ├── exception/                    # Global exception handling
│   │   │   ├── repository/                   # Spring Data JPA Repositories
│   │   │   ├── security/                     # BCrypt & JWT Authentication
│   │   │   └── service/                      # Business logic & Calculations
│   │   └── resources/
│   │       ├── application.properties        # MySQL configuration
│   │       ├── application-dev.properties    # H2 in-memory dev profile
│   │       ├── schema.sql
│   │       └── data.sql
│   └── test/java/com/smarthome/tracker/      # JUnit 5 & Mockito test suites
│
└── frontend/ (Root Static Web Files)         # Modern SaaS Responsive UI
    ├── index.html                            # Landing page
    ├── login.html                            # Sign In with 1-click Demo credentials
    ├── register.html                         # New user registration
    ├── dashboard.html                        # Master Analytics Dashboard
    ├── expenses.html                         # Expenses CRUD & CSV export
    ├── budgets.html                          # Budget Planner & 80%/100% alerts
    ├── maintenance.html                      # Maintenance tasks & priorities
    ├── calendar.html                         # Scheduler & recurring routines
    ├── bills.html                            # Household bills & payment records
    ├── service-providers.html                # Verified technician directory
    ├── reports.html                          # Financial analytics & reports
    ├── profile.html                          # Profile & password management
    └── assets/
        ├── css/style.css                     # Dark navy SaaS theme tokens
        └── js/
            ├── api.js                        # Unified REST API client
            ├── common.js                     # Toasts, modals, theme toggler, sidebar
            └── chart-runner.js               # Retina HTML5 Canvas charting engine
```

---

## 🚀 How to Run the Application

### Option A: 1-Click Instant Run (Active Local Server)

The application includes a standalone server (`server.py`) that implements the exact identical REST endpoints and relational schema using Python's standard library and SQLite.

1. **Start the Server**:
   ```powershell
   python server.py
   ```
2. **Access the Application**:
   Open your browser and navigate to:
   ```
   http://localhost:8080
   ```
3. **Log in with Demo Account**:
   - **Email:** `rahul.sharma@example.in`
   - **Password:** `demo123`
   *(Or click the "⚡ Quick Demo Credentials -> Auto-Fill" button on the login screen)*

---

### Option B: Spring Boot Backend with MySQL (IntelliJ IDEA / Maven)

When running in an environment with Maven and MySQL installed:

1. **Set Up MySQL Database**:
   Open MySQL CLI or MySQL Workbench:
   ```sql
   CREATE DATABASE smarthome_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
   Execute `schema.sql` and `data.sql`:
   ```bash
   mysql -u root -p smarthome_db < schema.sql
   mysql -u root -p smarthome_db < data.sql
   ```

2. **Configure Database Credentials**:
   Edit `src/main/resources/application.properties` or set environment variables:
   ```properties
   spring.datasource.url=jdbc:mysql://localhost:3306/smarthome_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Kolkata
   spring.datasource.username=root
   spring.datasource.password=your_mysql_password
   ```

3. **Build and Run with Maven**:
   ```bash
   mvn clean spring-boot:run
   ```
   Alternatively, open the project in **IntelliJ IDEA**, let Maven import dependencies, and run `SmartHomeTrackerApplication.java`.

4. **Open in Browser**:
   Navigate to `http://localhost:8080/index.html` or `http://localhost:8080/dashboard.html`.

---

## 🧪 Automated Testing

### Run Python E2E API & Logic Tests:
```powershell
python -m unittest test_app.py
```
This tests:
- Demo seed data integrity
- JWT token encryption and HMAC-SHA256 signature verification
- Positive expense amount validation
- Dynamic budget utilization percentage calculations
- Automated overdue task calculation when past deadline
- Duplicate bill payment prevention
- Indian Rupee currency formatting

### Run Spring Boot JUnit Tests:
```bash
mvn test
```
Executes `BudgetCalculationTest.java`, `MaintenanceStatusTest.java`, and `ExpenseServiceTest.java`.

---

## 🎨 UI/UX Design System Highlights

- **Palette**: Dark Navy (`#0f172a`, `#1e293b`), Crisp White Cards, Soft Slate Gray (`#f8fafc`), and Vibrant Teal (`#0d9488`, `#14b8a6`).
- **Typography**: Clean Outfit & Inter typography.
- **Theme**: Seamless Light / Dark mode toggle with instant persistence.
- **Feedback**: Non-blocking toast notifications, confirmation dialogs for destructive actions, and clear form field validations.
- **Offline Readiness**: Self-contained HTML5 Canvas Chart runner (`chart-runner.js`) ensuring graphs and analytics render without relying on external CDN dependencies.
