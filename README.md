# Interview Prep AI (Flask + Groq)

Users pick a role, experience level and categories, and get **AI-generated** interview questions,
then practice answering and get AI feedback. Visitors never need an API key: yours stays on the server.

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env      # put YOUR Groq key in GROQ_API_KEY
python server.py
```
Open http://localhost:3000 (use the server URL, not double-click on index.html).

## Files
- `server.py` - Flask app: `/generate-questions`, `/get-feedback`, `/health`
- `public/index.html` - the UI
- `.env` - your secret key (never commit; it is in `.gitignore`)

## Deploy (Render)
1. Push this repo to GitHub (without `.env`).
2. render.com -> New -> Web Service -> connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn server:app`
5. Environment -> add `GROQ_API_KEY` (and optionally `GROQ_MODEL`).

`RATE_LIMIT_PER_MIN` (default 20) limits requests per visitor IP to protect your Groq quota.
If Groq retires the default model, set `GROQ_MODEL` (https://console.groq.com/docs/models).
