-- Smart Home Expense & Maintenance Tracker
-- Database Schema for MySQL 8.0+

CREATE DATABASE IF NOT EXISTS smarthome_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smarthome_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(255),
    currency VARCHAR(10) DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB;

-- 2. Service Providers Directory
CREATE TABLE IF NOT EXISTS service_providers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    technician_name VARCHAR(100),
    service_category VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    email VARCHAR(150),
    address VARCHAR(255),
    service_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_sp_user (user_id),
    INDEX idx_sp_category (service_category)
) ENGINE=InnoDB;

-- 3. Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(80) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    expense_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    vendor VARCHAR(150),
    receipt_filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_expenses_user (user_id),
    INDEX idx_expenses_date (expense_date),
    INDEX idx_expenses_category (category)
) ENGINE=InnoDB;

-- 4. Budgets Table (Monthly overall & category targets)
CREATE TABLE IF NOT EXISTS budgets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    month_year VARCHAR(7) NOT NULL, -- Format: YYYY-MM
    total_budget DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_month (user_id, month_year),
    INDEX idx_budget_user_month (user_id, month_year)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS category_budgets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    budget_id BIGINT NOT NULL,
    category VARCHAR(80) NOT NULL,
    budget_limit DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE,
    UNIQUE KEY uk_budget_category (budget_id, category)
) ENGINE=InnoDB;

-- 5. Maintenance Tasks Table
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    service_provider_id BIGINT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(80) NOT NULL,
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') NOT NULL DEFAULT 'MEDIUM',
    status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE') NOT NULL DEFAULT 'PENDING',
    scheduled_date DATE,
    due_date DATE NOT NULL,
    completion_date DATE,
    estimated_cost DECIMAL(12, 2) DEFAULT 0.00,
    actual_cost DECIMAL(12, 2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_provider_id) REFERENCES service_providers(id) ON DELETE SET NULL,
    INDEX idx_maint_user (user_id),
    INDEX idx_maint_status (status),
    INDEX idx_maint_due (due_date)
) ENGINE=InnoDB;

-- 6. Recurring Maintenance Schedules
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(80) NOT NULL,
    frequency ENUM('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUAL') NOT NULL,
    preferred_day_of_month INT DEFAULT 1,
    next_due_date DATE NOT NULL,
    estimated_cost DECIMAL(12, 2) DEFAULT 0.00,
    service_provider_id BIGINT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_provider_id) REFERENCES service_providers(id) ON DELETE SET NULL,
    INDEX idx_sched_user (user_id)
) ENGINE=InnoDB;

-- 7. Household Bills
CREATE TABLE IF NOT EXISTS bills (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(80) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    billing_period VARCHAR(50) NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('UNPAID', 'PAID', 'OVERDUE') NOT NULL DEFAULT 'UNPAID',
    payment_date DATE,
    reference_number VARCHAR(100),
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_bills_user (user_id),
    INDEX idx_bills_status (status),
    INDEX idx_bills_due (due_date)
) ENGINE=InnoDB;

-- 8. Bill Payments History
CREATE TABLE IF NOT EXISTS bill_payments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bill_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    amount_paid DECIMAL(12, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_bp_bill (bill_id),
    INDEX idx_bp_user (user_id)
) ENGINE=InnoDB;

-- 9. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('INFO', 'WARNING', 'ALERT', 'SUCCESS') DEFAULT 'INFO',
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notif_user_read (user_id, is_read)
) ENGINE=InnoDB;
