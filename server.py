"""
Interview Prep AI - Flask backend (AI-generated questions only)

Serves public/index.html and two API endpoints:
  POST /generate-questions  -> AI-generated interview questions (Groq)
  POST /get-feedback        -> AI feedback on a practice answer

The Groq API key lives in the server's environment and is never sent to the browser,
so visitors never need their own key.
"""

import json
import os
import re
import time
import uuid
from collections import defaultdict, deque

from flask import Flask, jsonify, request, send_from_directory

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from groq import Groq
except ImportError:
    Groq = None

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
PORT = int(os.getenv("PORT", "3000"))
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))

CATEGORIES = ["Technical", "Behavioral", "HR"]
EXPERIENCE_LEVELS = {
    "Fresher": "Fresher / Entry Level",
    "Mid-level": "Mid-level (2-5 yrs)",
    "Senior": "Senior (5+ yrs)",
}

app = Flask(__name__, static_folder="public", static_url_path="")


class ConfigError(RuntimeError):
    """Server is missing the key or the groq package (a developer problem, not the user's)."""


# --------------------------------------------------------------------------- #
# Simple per-IP rate limit (protects your Groq quota on a public deployment)
# --------------------------------------------------------------------------- #
_hits = defaultdict(deque)


@app.before_request
def rate_limit():
    if request.method != "POST":
        return None
    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "unknown").split(",")[0].strip()
    now = time.time()
    hits = _hits[ip]
    while hits and now - hits[0] > 60:
        hits.popleft()
    if len(hits) >= RATE_LIMIT_PER_MIN:
        return jsonify(success=False, error="Too many requests. Please wait a minute and try again."), 429
    hits.append(now)
    return None


# --------------------------------------------------------------------------- #
# Groq helpers
# --------------------------------------------------------------------------- #
def split_count(total: int, parts: int):
    base, rem = divmod(total, parts)
    return [base + (1 if i < rem else 0) for i in range(parts)]


def extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def call_groq_json(system: str, user: str, temperature: float = 0.7):
    if Groq is None:
        raise ConfigError("The 'groq' package is not installed.")
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ConfigError("GROQ_API_KEY is not set.")

    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
    except Exception as err:
        # Some models don't support JSON mode - retry without it.
        msg = str(err).lower()
        if "response_format" in msg or "json" in msg:
            resp = client.chat.completions.create(model=GROQ_MODEL, messages=messages, temperature=temperature)
        else:
            raise
    return extract_json(resp.choices[0].message.content)


def ai_questions(role, experience, categories, count):
    distribution = ", ".join(f"{n} {c}" for c, n in zip(categories, split_count(count, len(categories))))
    system = (
        "You are a senior interviewer and hiring manager. You write realistic, specific interview "
        "questions tailored to the role and seniority. Respond with a single valid JSON object only."
    )
    user = f"""Generate exactly {count} interview questions.

Role: {role}
Experience level: {EXPERIENCE_LEVELS[experience]}
Distribution by category: {distribution}

Rules:
- category must be one of: {", ".join(categories)}
- difficulty must be one of: Easy, Medium, Hard, and should suit the experience level
- Technical questions must be specific to the role's real tools, skills and problems (include scenario-based ones)
- Every question must be different; avoid generic filler
- "tip" is one short sentence describing what a strong answer should cover

Return JSON in exactly this shape:
{{"questions": [{{"category": "...", "difficulty": "...", "question": "...", "tip": "..."}}]}}"""

    data = call_groq_json(system, user, temperature=0.8)
    raw = data.get("questions", []) if isinstance(data, dict) else data
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        cat = str(item.get("category", "")).strip().title()
        if cat == "Hr":
            cat = "HR"
        if cat not in categories:
            cat = categories[0]
        diff = str(item.get("difficulty", "Medium")).strip().title()
        if diff not in ("Easy", "Medium", "Hard"):
            diff = "Medium"
        q = str(item.get("question", "")).strip()
        if not q:
            continue
        out.append(
            {
                "id": uuid.uuid4().hex[:8],
                "category": cat,
                "question": q,
                "difficulty": diff,
                "source": "AI",
                "tip": str(item.get("tip", "")).strip(),
            }
        )
    if not out:
        raise ValueError("Model returned no usable questions.")
    return out[:count]


def friendly_error(err: Exception, action: str):
    """Log the real error server-side; show users a safe, simple message."""
    app.logger.error("%s failed: %s", action, err)
    if isinstance(err, ConfigError):
        return "The AI service is not set up yet. Please contact the site owner."
    return f"Could not {action} right now. Please try again."


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    return jsonify(ok=True, groq_key_set=bool(os.getenv("GROQ_API_KEY", "").strip()), model=GROQ_MODEL)


@app.post("/generate-questions")
def generate_questions():
    body = request.get_json(silent=True) or {}

    role = str(body.get("role", "")).strip()[:100]
    if not role:
        return jsonify(success=False, error="Please select or enter a role."), 400
    experience = body.get("experience") if body.get("experience") in EXPERIENCE_LEVELS else "Fresher"
    categories = [c for c in body.get("categories", []) if c in CATEGORIES] or CATEGORIES
    try:
        count = max(3, min(10, int(body.get("count", 5))))
    except (TypeError, ValueError):
        count = 5

    try:
        questions = ai_questions(role, experience, categories, count)
    except Exception as err:
        return jsonify(success=False, error=friendly_error(err, "generate questions")), 502

    return jsonify(success=True, questions=questions, warnings=[])


@app.post("/get-feedback")
def get_feedback():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()[:1000]
    answer = str(body.get("answer", "")).strip()[:4000]
    role = str(body.get("role", "")).strip()[:100] or "Software Engineer"
    experience = body.get("experience") if body.get("experience") in EXPERIENCE_LEVELS else "Fresher"

    if not question or not answer:
        return jsonify(success=False, error="Both a question and an answer are required."), 400

    system = (
        "You are a supportive but honest interview coach. Evaluate the candidate's answer. "
        "Respond with a single valid JSON object only."
    )
    user = f"""Role: {role}
Experience level: {EXPERIENCE_LEVELS[experience]}
Interview question: {question}
Candidate's answer: {answer}

Return JSON in exactly this shape:
{{"score": <integer 1-10>, "strength": "<what was good, 1-2 sentences>", "improvement": "<the most important thing to improve, 1-2 sentences>", "better_answer": "<a concise example of a stronger answer, 3-5 sentences>"}}"""

    try:
        data = call_groq_json(system, user, temperature=0.3)
    except Exception as err:
        return jsonify(success=False, error=friendly_error(err, "get feedback")), 502

    return jsonify(
        success=True,
        feedback={
            "score": data.get("score", "-"),
            "strength": data.get("strength", ""),
            "improvement": data.get("improvement", ""),
            "better_answer": data.get("better_answer", ""),
        },
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=True)