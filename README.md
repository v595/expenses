# Expense Tracker

A full-stack personal expense tracker built as a learning project: React (Vite) frontend, Flask REST API backend, SQLite database.

## Features

- Register / login / logout (token-based auth)
- Add, edit, delete, and view transactions (income or expense)
- Search and filter transactions by category, type, and date range
- Dashboard: total income, total expenses, balance, transaction count, top spending category, category breakdown
- Per-user data isolation — users only ever see their own transactions
- Full input validation and consistent JSON error responses on the API

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), React Router |
| Backend | Python, Flask |
| Database | SQLite 3 |
| Auth | Token-based (Bearer token in `Authorization` header) |
| Testing | pytest (backend) |

## Architecture

```
React (localhost:5173)
   |  HTTP / JSON
   v
Flask REST API (localhost:5000)
   |  routes -> services -> models
   v
SQLite (backend/database/expense_tracker.db)
```

- **Routes** (`app/routes/`) — thin HTTP handlers, no business logic
- **Services** (`app/services/`) — validation and business logic
- **Models** (`app/models/`) — raw SQL against SQLite

## Project Structure

```
expense-tracker/
├── backend/
│   ├── app/
│   │   ├── routes/        (health, auth, transactions, dashboard)
│   │   ├── models/        (user, transaction — raw SQL)
│   │   ├── services/      (business logic + validation)
│   │   ├── __init__.py    (app factory)
│   │   ├── config.py
│   │   └── database.py
│   ├── database/           (SQLite file, gitignored)
│   ├── tests/               (pytest suite)
│   ├── run.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/    (Navbar, TransactionForm, TransactionList, SummaryCard)
│   │   ├── pages/          (Login, Register, Dashboard, Transactions)
│   │   ├── context/         (AuthContext)
│   │   ├── services/        (api.js — all backend calls)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── .env.example
├── .gitignore
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # Windows
# source venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
```

Copy `.env.example` to `.env` and adjust if needed (optional — safe defaults are used otherwise):

```bash
cp .env.example .env
```

Run the server:

```bash
./venv/Scripts/python run.py   # Windows
# venv/bin/python run.py       # macOS/Linux
```

Backend runs at **http://localhost:5000**. Verify with `GET /api/health`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at **http://localhost:5173**.

### Database

SQLite tables are created automatically on first backend startup — no manual setup needed. The database file lives at `backend/database/expense_tracker.db` and is gitignored (regenerated automatically).

## Running Tests

```bash
cd backend
./venv/Scripts/python -m pytest tests/ -v
```

## API Reference

All endpoints are prefixed with `/api`. Protected endpoints require `Authorization: Bearer <token>`.

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create an account, returns a token |
| POST | `/auth/login` | — | Log in, returns a token |
| GET | `/auth/me` | ✓ | Get the current user |
| POST | `/auth/logout` | ✓ | Invalidate the current token |

### Transactions
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/transactions` | ✓ | List transactions (supports `?category=`, `?type=`, `?start_date=`, `?end_date=`, `?search=`) |
| GET | `/transactions/<id>` | ✓ | Get one transaction |
| POST | `/transactions` | ✓ | Create a transaction |
| PUT | `/transactions/<id>` | ✓ | Update a transaction |
| DELETE | `/transactions/<id>` | ✓ | Delete a transaction |

### Dashboard
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/dashboard/summary` | ✓ | Income, expenses, balance, category breakdown |
| GET | `/dashboard/monthly` | ✓ | Income/expenses grouped by month |

### Error format

```json
{ "error": "Transaction not found" }
```

Status codes used: `200`, `201`, `400`, `401`, `404`, `405`, `409`, `500`.

## Security Notes

- Passwords are hashed with `werkzeug.security` — never stored or returned in plaintext
- Auth uses opaque bearer tokens (not cookies), avoiding cross-origin cookie issues since frontend and backend run on different origins
- Every transaction route checks that the resource belongs to the authenticated user (returns 404, not 403, to avoid revealing existence of other users' data)
- All SQL uses parameterized queries — no string-built SQL from user input
- Secrets are read from environment variables, never hardcoded or committed

## Future Improvements

- Charts (spending over time, category pie chart) using the existing `/dashboard/monthly` endpoint
- Budgets and recurring expenses
- CSV export
- PostgreSQL for production
- Deployment (Vercel + Render)
- MCP server for AI integration
