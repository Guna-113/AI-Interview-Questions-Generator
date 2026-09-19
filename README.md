# Interview Prep AI (Flask + Groq)

Your original HTML frontend, with a Python backend and three question modes:

- **Built-in**: curated Technical / Behavioral / HR bank (frontend, backend, data, DevOps, QA, general). No API key needed.
- **AI-generated**: fresh role-specific questions from a Groq model, each with a "what a strong answer covers" tip.
- **Both**: N built-in + N AI questions (AI avoids repeating the built-in ones).

Practice mode sends your answer to Groq for a 1-10 score, strength, improvement and a sample stronger answer.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env      # paste your key from https://console.groq.com
python server.py
```

Open http://localhost:3000

## Files

- `server.py` - Flask app: `/generate-questions`, `/get-feedback`, `/health`
- `questions_bank.py` - built-in questions and selection logic
- `public/index.html` - frontend (open it via the server, not by double-clicking)

The API key lives only in `.env` on the server and is never sent to the browser.
If Groq retires the default model, set `GROQ_MODEL` in `.env` (see https://console.groq.com/docs/models).

## Deploy

Any Python host (Render, Railway, etc.). Set `GROQ_API_KEY` as an environment variable and run with
`gunicorn server:app` (add `gunicorn` to requirements).
