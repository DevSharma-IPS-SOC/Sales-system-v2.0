# 📊 Sales Analysis System — Upgraded Version

## Features

### ✅ New in This Version

#### 1. Customer & Billing Module
- **Customer Management** — Add, edit, view customers with name, phone, email, address, GST
- **Linked Sales** — Every sale can be linked to a customer
- **Invoice Generation** — Auto-generated printable invoices (INV-00001 format)
- **Invoice History** — Filter invoices by customer, date range
- **Walk-in Customer** support for quick sales without registration

#### 2. Enhanced Analytics
- **Overview Dashboard** — Top 5 / Bottom 5 products, monthly revenue vs profit bar chart
- **Sales Trends** — Filter by month/custom dates, per-product line chart
- **Product Analysis** — 6-month trend for individual products (revenue + profit)
- **Advanced Forecasting** — Moving average of last 3 months, three modes:
  - Conservative ×1.2 | Normal ×1.5 | Aggressive ×2.0
- **Category Analytics** — Pie chart (revenue share) + bar chart (profit contribution)

#### 3. Role-Based Authentication
- **Admin** — Full access: inventory CRUD, user management, all analytics, logs
- **Salesperson** — Sell items, view stock, generate invoices, view customers
- **User Creation** — Admins can create accounts and assign roles
- **Activity Logs** — Every action logged: who did what, when

---

## Setup & Run

```bash
# 1. Install dependency
pip install flask

# 2. Run the app
python app.py

# 3. Open browser
http://localhost:5000
```

**Default Login:** `Admin` / `Admin123`

---

## File Structure

```
sales_system/
├── app.py                 # Main Flask backend (all API routes)
├── requirements.txt
├── data.json              # Inventory data
├── sales.json             # Sales records
├── customers.json         # Customer data
├── users.json             # Users with hashed passwords
├── activity_logs.json     # Audit trail
└── templates/
    ├── login.html         # Login page
    ├── dashboard.html     # Inventory dashboard (role-aware)
    ├── analytics.html     # 5-tab analytics dashboard
    ├── customers.html     # Customers + Invoice history
    ├── invoice.html       # Printable invoice page
    ├── admin_users.html   # User management (admin only)
    └── admin_logs.html    # Activity logs (admin only)
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/login` | — | Login |
| GET | `/api/items` | Any | Get inventory |
| POST | `/api/items` | Admin | Add item |
| PUT | `/api/items/<id>` | Admin | Update item |
| DELETE | `/api/items/<id>` | Admin | Delete item |
| GET | `/api/search?q=` | Any | Search items |
| POST | `/api/sell` | Any | Record sale |
| GET | `/api/sales` | Any | All sales |
| GET | `/api/invoice/<id>` | Any | Get invoice data |
| GET | `/api/invoices` | Any | Invoice history |
| GET | `/api/customers` | Any | All customers |
| POST | `/api/customers` | Any | Add customer |
| PUT | `/api/customers/<id>` | Any | Edit customer |
| GET | `/api/analytics/dashboard` | Any | Overview data |
| GET | `/api/analytics/forecast` | Any | Reorder forecast |
| GET | `/api/analytics/product/<name>` | Any | Product trend |
| GET | `/api/users` | Admin | List users |
| POST | `/api/users` | Admin | Create user |
| PUT | `/api/users/<id>` | Admin | Edit user |
| DELETE | `/api/users/<id>` | Admin | Delete user |
| GET | `/api/logs` | Admin | Activity logs |
