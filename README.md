## Google Gmail OAuth

### 1. Google Cloud Console

1. Create/select a Google Cloud project.
2. Enable **Gmail API**.
3. Configure the OAuth consent screen. For a personal/test app, add your Google account as a test user.
4. Create an OAuth client ID with application type **Web application**.
5. Add this exact authorized redirect URI:

   `http://localhost:8000/auth/google/callback`

Copy the client ID and secret to `.env`. Do not commit `.env` or `token.json`.

### 2. Run locally

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/auth/google` and approve read-only Gmail access. The refresh token is stored locally in `token.json`.

### 3. API

- `GET /auth/google` — start Google login
- `GET /auth/google/status` — check connection
- `GET /emails?max_results=20` — read message metadata (From, To, Subject, Date)
- `POST /sync-transactions?max_results=20` — fetch ACB emails, parse transactions, and insert new ones into the `transactions` table; existing transactions are skipped
- `GET /transactions/statistics?start_date=2026-10-01&end_date=2026-10-31` — authenticated statistics for the inclusive date range. The response contains `data.start_date`, `data.end_date`, `data.total_expense` (DEBIT), `data.total_income` (CREDIT), and `data.categories` as an array. Each category includes its ID, name, type, status, count, and transaction list. Every category is returned, including inactive categories; categories without transactions have `count: null` and `transactions: null`. Transactions without a category appear in an `Unknown` entry when present. That entry has `category_id`, `type`, and `status` set to `null`, and its nested transactions show `category_name: "Unknown"`. Totals include these transactions.

The statistics endpoint requires the login JWT in `Authorization: Bearer <token>` or the `auth_token` cookie set after Google login. Missing or invalid tokens return `401`; transaction data is filtered by the authenticated user's ID. Categories are shared records in the current database schema.

Example response (amounts are decimal strings):

```json
{
  "data": {
    "start_date": "2026-10-01",
    "end_date": "2026-10-31",
    "total_expense": "125000.00",
    "total_income": "3000000.00",
    "categories": [
      {
        "category_id": "a1b2c3d4-0000-4000-8000-000000000001",
        "name": "Food",
        "type": "expense",
        "status": "active",
        "count": 1,
        "transactions": [{ "transaction_id": "BANK-001", "amount": "125000.00" }]
      }
    ]
  }
}
```

The transaction objects contain the full fields returned by `GET /transactions`.

This starter implementation stores one connected Google account. For production/multiple users, store encrypted refresh tokens per user in a database and use a server-side OAuth state/session store instead of the in-memory state set.
