"""Built-in interview question bank and generator (no API key needed)."""

import random
import re
import uuid

EXPERIENCE_LEVELS = {
    "Fresher": "Fresher / Entry Level",
    "Mid-level": "Mid-level (2-5 yrs)",
    "Senior": "Senior (5+ yrs)",
}
CATEGORIES = ["Technical", "Behavioral", "HR"]

# (question, difficulty)
TECHNICAL = {
    "frontend": [
        ("What is the difference between `let`, `const` and `var` in JavaScript?", "Easy"),
        ("Explain the CSS box model and how `box-sizing` changes it.", "Easy"),
        ("What is semantic HTML and why does it matter for accessibility and SEO?", "Easy"),
        ("Explain closures in JavaScript with a practical example.", "Medium"),
        ("How does the event loop work? What is the difference between microtasks and macrotasks?", "Hard"),
        ("What is the virtual DOM, and how does reconciliation work in React?", "Medium"),
        ("When would you use `useMemo`, `useCallback` and `React.memo`? When do they hurt?", "Medium"),
        ("How do you debug and fix layout shifts and slow rendering on a page?", "Hard"),
        ("Explain CORS. Why does the browser block some cross-origin requests?", "Medium"),
        ("Compare client-side rendering, server-side rendering and static generation.", "Medium"),
        ("How would you architect state management for a large front-end application?", "Hard"),
        ("How do you make a web app accessible (ARIA, keyboard navigation, contrast)?", "Medium"),
    ],
    "backend": [
        ("What is the difference between REST and GraphQL?", "Easy"),
        ("Explain the difference between SQL and NoSQL databases and when to pick each.", "Easy"),
        ("What are HTTP status codes 200, 201, 400, 401, 403, 404 and 500 used for?", "Easy"),
        ("What is database indexing, and what are the trade-offs of adding an index?", "Medium"),
        ("Explain authentication vs authorization. How does JWT-based auth work?", "Medium"),
        ("What is the N+1 query problem and how do you fix it?", "Medium"),
        ("How would you design a rate limiter for a public API?", "Hard"),
        ("Explain ACID properties and database isolation levels.", "Hard"),
        ("How do you make an API idempotent? Why does it matter for payments?", "Hard"),
        ("How would you design a URL shortener that handles millions of requests per day?", "Hard"),
        ("What caching strategies do you know (cache-aside, write-through) and how do you handle invalidation?", "Medium"),
        ("What is the difference between processes, threads and async I/O?", "Medium"),
    ],
    "data": [
        ("What is the difference between supervised and unsupervised learning?", "Easy"),
        ("Explain overfitting and three ways to prevent it.", "Easy"),
        ("What is the difference between precision, recall and F1-score?", "Medium"),
        ("How do you handle missing values and outliers in a dataset?", "Medium"),
        ("Explain the bias-variance trade-off.", "Medium"),
        ("Write a SQL query to find the second-highest salary in each department.", "Medium"),
        ("What is cross-validation and why is it better than a single train/test split?", "Medium"),
        ("How would you handle a heavily imbalanced classification dataset?", "Hard"),
        ("Explain how a random forest differs from gradient boosting.", "Hard"),
        ("How would you design an A/B test and decide whether the result is statistically significant?", "Hard"),
        ("What are window functions in SQL? Give a use case.", "Medium"),
        ("How would you monitor a deployed ML model for drift?", "Hard"),
    ],
    "devops": [
        ("What is CI/CD and why is it useful?", "Easy"),
        ("Explain the difference between a container and a virtual machine.", "Easy"),
        ("What is Infrastructure as Code? Name a tool you have used.", "Easy"),
        ("Explain how Kubernetes schedules pods and what a Deployment does.", "Medium"),
        ("How would you design a zero-downtime deployment strategy?", "Medium"),
        ("What is the difference between blue/green and canary deployments?", "Medium"),
        ("A production service suddenly has high latency. Walk me through your debugging steps.", "Hard"),
        ("How do you manage secrets across environments securely?", "Medium"),
        ("What are SLIs, SLOs and error budgets?", "Hard"),
        ("How would you design monitoring and alerting for a microservices system?", "Hard"),
    ],
    "qa": [
        ("What is the difference between verification and validation?", "Easy"),
        ("Explain the testing pyramid.", "Easy"),
        ("How do you write a good bug report?", "Easy"),
        ("What is the difference between smoke, sanity and regression testing?", "Medium"),
        ("How do you decide what to automate and what to test manually?", "Medium"),
        ("How would you test a login page? List positive, negative and edge cases.", "Medium"),
        ("How do you deal with flaky tests?", "Hard"),
        ("How would you design a test strategy for a new payments feature?", "Hard"),
    ],
    "general": [
        ("Explain the difference between an array and a linked list. When would you use each?", "Easy"),
        ("What is Big-O notation? Explain with two examples.", "Easy"),
        ("What are the four pillars of object-oriented programming?", "Easy"),
        ("What is the difference between a stack and a queue?", "Easy"),
        ("Explain how a hash map works internally, including collisions.", "Medium"),
        ("What is the difference between a process and a thread?", "Medium"),
        ("How does Git branching work, and what is the difference between merge and rebase?", "Medium"),
        ("What happens when you type a URL into the browser and press Enter?", "Medium"),
        ("Explain SOLID principles with an example of a violation.", "Medium"),
        ("How would you find a cycle in a linked list?", "Medium"),
        ("What is deadlock and how can it be prevented?", "Hard"),
        ("Design a scalable notification system. What components would you need?", "Hard"),
    ],
}

BEHAVIORAL = [
    ("Tell me about yourself and why you are interested in this role.", "Easy"),
    ("Describe a time you had to meet a tight deadline under pressure.", "Easy"),
    ("Tell me about a time you worked effectively in a team.", "Easy"),
    ("Describe a time you made a mistake at work. How did you handle it?", "Medium"),
    ("Tell me about a time you disagreed with a teammate or manager. What happened?", "Medium"),
    ("Describe a situation where you had to learn something new very quickly.", "Medium"),
    ("Give an example of a time you took initiative without being asked.", "Medium"),
    ("Tell me about a time you received critical feedback. How did you respond?", "Medium"),
    ("Describe your most challenging project and how you overcame the obstacles.", "Hard"),
    ("Tell me about a time you had to influence others without formal authority.", "Hard"),
    ("Describe a time you had to make a decision with incomplete information.", "Hard"),
    ("Tell me about a time you led a team through a failure or a missed deadline.", "Hard"),
]

HR = [
    ("Why do you want to work for our company?", "Easy"),
    ("What are your greatest strengths?", "Easy"),
    ("What is your biggest weakness, and what are you doing about it?", "Easy"),
    ("Where do you see yourself professionally in three years?", "Easy"),
    ("Why are you leaving your current job (or why did you leave your last one)?", "Medium"),
    ("What are your salary expectations?", "Medium"),
    ("How do you handle stress and competing priorities?", "Medium"),
    ("What kind of work environment do you thrive in?", "Medium"),
    ("Are you open to relocation or a hybrid/remote arrangement?", "Easy"),
    ("How would your previous manager or colleagues describe you?", "Medium"),
    ("What motivates you to do your best work?", "Easy"),
    ("Do you have any questions for us?", "Easy"),
]

DOMAIN_KEYWORDS = {
    "frontend": ["frontend", "front-end", "front end", "react", "angular", "vue", "ui", "web", "javascript", "css"],
    "backend": ["backend", "back-end", "back end", "node", "java", "django", "flask", "spring", "api", "server", "python"],
    "data": ["data", "machine learning", "ml", "ai", "analyst", "scientist", "analytics", "bi"],
    "devops": ["devops", "sre", "cloud", "infrastructure", "platform", "kubernetes", "site reliability"],
    "qa": ["qa", "tester", "testing", "quality", "sdet", "test engineer"],
}

# Weights: how likely each difficulty is to be picked for each experience level
DIFF_WEIGHTS = {
    "Fresher": {"Easy": 3.0, "Medium": 2.0, "Hard": 0.4},
    "Mid-level": {"Easy": 1.0, "Medium": 3.0, "Hard": 1.5},
    "Senior": {"Easy": 0.4, "Medium": 2.0, "Hard": 3.0},
}


# --------------------------------------------------------------------------- #
# Built-in generator
# --------------------------------------------------------------------------- #
def detect_domain(role: str):
    """Return (domain, matched) - matched=False means we fell back to 'general'."""
    role_l = role.lower()
    for domain, words in DOMAIN_KEYWORDS.items():
        for w in words:
            if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", role_l):
                return domain, True
    return "general", False


def split_count(total: int, parts: int):
    base, rem = divmod(total, parts)
    return [base + (1 if i < rem else 0) for i in range(parts)]


def weighted_sample(items, k, experience):
    """Weighted sampling without replacement (Efraimidis-Spirakis)."""
    weights = DIFF_WEIGHTS[experience]
    keyed = [(random.random() ** (1.0 / weights[d]), (q, d)) for q, d in items]
    keyed.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in keyed[:k]]


def builtin_questions(role, experience, categories, count):
    domain, _ = detect_domain(role)
    banks = {"Technical": TECHNICAL[domain], "Behavioral": BEHAVIORAL, "HR": HR}
    out = []
    for cat, n in zip(categories, split_count(count, len(categories))):
        for q, d in weighted_sample(banks[cat], n, experience):
            out.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "category": cat,
                    "question": q,
                    "difficulty": d,
                    "source": "Built-in",
                    "tip": "",
                }
            )
    return out
