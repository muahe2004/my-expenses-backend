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
- `POST /sync-transactions?max_results=20` — fetch ACB emails, parse transactions, and upsert them into the `transactions` table

This starter implementation stores one connected Google account. For production/multiple users, store encrypted refresh tokens per user in a database and use a server-side OAuth state/session store instead of the in-memory state set.
