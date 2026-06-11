"""
Agent 3: Roadmap Generator
Responsibilities: Personalized learning roadmap → daily/weekly/monthly plans → resources → mock interviews

Resource Fix: Groq hallucinates URLs. We use a curated database of verified URLs
per skill/platform, then let Groq only generate plans (not URLs).
"""
import re
import json
import math
from typing import List, Dict, Any

from groq import Groq
from app.core.config import settings

_client = Groq(api_key=settings.GROQ_API_KEY)


import time

_last_call_time = 0.0
_MIN_INTERVAL   = 2.0

def _groq(prompt: str) -> str:
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call_time = time.time()

    for attempt in range(3):
        try:
            response = _client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            content = response.choices[0].message.content.strip()
            if content:
                return content
        except Exception as e:
            if "AuthenticationError" in type(e).__name__ or "invalid_api_key" in str(e):
                raise
            if "RateLimitError" in type(e).__name__:
                raise
            if attempt == 2:
                raise
    return "{}"


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


# ─── Curated Resource Database ────────────────────────────────────────────────
# Verified, working URLs organized by skill keyword → list of resources
# Each resource: {title, url, type, duration}

_RESOURCE_DB: Dict[str, List[Dict[str, Any]]] = {
    # ── Python ──────────────────────────────────────────────────────────────
    "python": [
        {"title": "Python for Everybody – Full Course",         "url": "https://www.youtube.com/watch?v=8DvywoWv6fI",      "type": "Video",    "duration": "14 hrs"},
        {"title": "Python Tutorial – freeCodeCamp",             "url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/", "type": "Course", "duration": "6 hrs"},
        {"title": "Python Exercises – W3Schools",               "url": "https://www.w3schools.com/python/python_exercises.asp", "type": "Practice", "duration": "2 hrs"},
    ],
    # ── Java ────────────────────────────────────────────────────────────────
    "java": [
        {"title": "Java Full Course – Telusko",                 "url": "https://www.youtube.com/watch?v=GoXwIVyNvX0",      "type": "Video",    "duration": "13 hrs"},
        {"title": "Java Programming – Codecademy",              "url": "https://www.codecademy.com/learn/learn-java",       "type": "Course",   "duration": "25 hrs"},
        {"title": "Java Practice – HackerRank",                 "url": "https://www.hackerrank.com/domains/java",           "type": "Practice", "duration": "3 hrs"},
    ],
    # ── Data Structures & Algorithms ────────────────────────────────────────
    "data structures": [
        {"title": "DSA Full Course – Abdul Bari",               "url": "https://www.youtube.com/watch?v=0IAPZzGSbME",      "type": "Video",    "duration": "24 hrs"},
        {"title": "DSA – GeeksforGeeks",                        "url": "https://www.geeksforgeeks.org/data-structures/",    "type": "Article",  "duration": "5 hrs"},
        {"title": "LeetCode DSA Practice",                      "url": "https://leetcode.com/explore/learn/",               "type": "Practice", "duration": "10 hrs"},
    ],
    "algorithms": [
        {"title": "Algorithms – Abdul Bari",                    "url": "https://www.youtube.com/watch?v=0IAPZzGSbME",      "type": "Video",    "duration": "24 hrs"},
        {"title": "Algorithms – GeeksforGeeks",                 "url": "https://www.geeksforgeeks.org/fundamentals-of-algorithms/", "type": "Article", "duration": "4 hrs"},
        {"title": "LeetCode Top 150 Practice",                  "url": "https://leetcode.com/studyplan/top-interview-150/", "type": "Practice", "duration": "20 hrs"},
    ],
    # ── SQL / Databases ─────────────────────────────────────────────────────
    "sql": [
        {"title": "SQL Full Course – freeCodeCamp",             "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY",      "type": "Video",    "duration": "4 hrs"},
        {"title": "SQL Tutorial – W3Schools",                   "url": "https://www.w3schools.com/sql/",                    "type": "Article",  "duration": "3 hrs"},
        {"title": "SQL Practice – HackerRank",                  "url": "https://www.hackerrank.com/domains/sql",            "type": "Practice", "duration": "3 hrs"},
    ],
    "mysql": [
        {"title": "MySQL Crash Course – Traversy Media",        "url": "https://www.youtube.com/watch?v=9ylj9NR0Lcg",      "type": "Video",    "duration": "1.5 hrs"},
        {"title": "MySQL Tutorial – W3Schools",                 "url": "https://www.w3schools.com/mysql/",                  "type": "Article",  "duration": "2 hrs"},
    ],
    "postgresql": [
        {"title": "PostgreSQL Full Course – freeCodeCamp",      "url": "https://www.youtube.com/watch?v=qw--VYLpxG4",      "type": "Video",    "duration": "4 hrs"},
        {"title": "PostgreSQL Tutorial",                        "url": "https://www.postgresqltutorial.com/",               "type": "Article",  "duration": "3 hrs"},
    ],
    "mongodb": [
        {"title": "MongoDB Crash Course – Traversy Media",      "url": "https://www.youtube.com/watch?v=-56x56UppqQ",      "type": "Video",    "duration": "1.5 hrs"},
        {"title": "MongoDB University – Free Courses",          "url": "https://learn.mongodb.com/",                        "type": "Course",   "duration": "5 hrs"},
    ],
    # ── Web Frontend ────────────────────────────────────────────────────────
    "html": [
        {"title": "HTML Full Course – freeCodeCamp",            "url": "https://www.freecodecamp.org/learn/responsive-web-design/", "type": "Course", "duration": "10 hrs"},
        {"title": "HTML Tutorial – W3Schools",                  "url": "https://www.w3schools.com/html/",                   "type": "Article",  "duration": "2 hrs"},
    ],
    "css": [
        {"title": "CSS Full Course – freeCodeCamp",             "url": "https://www.freecodecamp.org/learn/responsive-web-design/", "type": "Course", "duration": "10 hrs"},
        {"title": "CSS Tutorial – W3Schools",                   "url": "https://www.w3schools.com/css/",                    "type": "Article",  "duration": "2 hrs"},
        {"title": "Flexbox Froggy – CSS Practice",              "url": "https://flexboxfroggy.com/",                        "type": "Practice", "duration": "1 hr"},
    ],
    "javascript": [
        {"title": "JavaScript Full Course – freeCodeCamp",      "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "type": "Course", "duration": "30 hrs"},
        {"title": "JavaScript – The Odin Project",              "url": "https://www.theodinproject.com/paths/full-stack-javascript", "type": "Course", "duration": "20 hrs"},
        {"title": "JavaScript Practice – HackerRank",           "url": "https://www.hackerrank.com/domains/tutorials/10-days-of-javascript", "type": "Practice", "duration": "5 hrs"},
    ],
    "typescript": [
        {"title": "TypeScript Full Course – Traversy Media",    "url": "https://www.youtube.com/watch?v=BCg4U1FzODs",      "type": "Video",    "duration": "2 hrs"},
        {"title": "TypeScript Handbook – Official Docs",        "url": "https://www.typescriptlang.org/docs/handbook/intro.html", "type": "Article", "duration": "3 hrs"},
    ],
    "react": [
        {"title": "React Full Course – freeCodeCamp",           "url": "https://www.youtube.com/watch?v=bMknfKXIFA8",      "type": "Video",    "duration": "12 hrs"},
        {"title": "React Official Tutorial",                    "url": "https://react.dev/learn",                           "type": "Article",  "duration": "4 hrs"},
        {"title": "React Projects – Scrimba",                   "url": "https://scrimba.com/learn/learnreact",              "type": "Course",   "duration": "6 hrs"},
    ],
    "react native": [
        {"title": "React Native – Full Course freeCodeCamp",    "url": "https://www.youtube.com/watch?v=0-S5a0eXPoc",      "type": "Video",    "duration": "8 hrs"},
        {"title": "React Native Official Docs",                 "url": "https://reactnative.dev/docs/getting-started",      "type": "Article",  "duration": "3 hrs"},
    ],
    # ── Backend Frameworks ──────────────────────────────────────────────────
    "django": [
        {"title": "Django Full Course – freeCodeCamp",          "url": "https://www.youtube.com/watch?v=F5mRW0jo-U4",      "type": "Video",    "duration": "6 hrs"},
        {"title": "Django Official Tutorial",                   "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "type": "Article", "duration": "3 hrs"},
    ],
    "flask": [
        {"title": "Flask Tutorial – Corey Schafer",             "url": "https://www.youtube.com/watch?v=MwZwr5Tvyxo",      "type": "Video",    "duration": "5 hrs"},
        {"title": "Flask Official Docs",                        "url": "https://flask.palletsprojects.com/en/stable/quickstart/", "type": "Article", "duration": "2 hrs"},
    ],
    "fastapi": [
        {"title": "FastAPI Full Course – freeCodeCamp",         "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",      "type": "Video",    "duration": "5 hrs"},
        {"title": "FastAPI Official Tutorial",                  "url": "https://fastapi.tiangolo.com/tutorial/",            "type": "Article",  "duration": "3 hrs"},
    ],
    "spring boot": [
        {"title": "Spring Boot Full Course – Amigoscode",       "url": "https://www.youtube.com/watch?v=9SGDpanrc8U",      "type": "Video",    "duration": "4 hrs"},
        {"title": "Spring Boot Guide – Baeldung",               "url": "https://www.baeldung.com/spring-boot",              "type": "Article",  "duration": "3 hrs"},
    ],
    "node.js": [
        {"title": "Node.js Full Course – freeCodeCamp",         "url": "https://www.youtube.com/watch?v=Oe421EPjeBE",      "type": "Video",    "duration": "8 hrs"},
        {"title": "Node.js Official Docs",                      "url": "https://nodejs.org/en/docs/guides/",                "type": "Article",  "duration": "2 hrs"},
    ],
    # ── Cloud & DevOps ──────────────────────────────────────────────────────
    "aws": [
        {"title": "AWS Cloud Practitioner – freeCodeCamp",      "url": "https://www.youtube.com/watch?v=SOTamWNgDKc",      "type": "Video",    "duration": "14 hrs"},
        {"title": "AWS Skill Builder – Free Courses",           "url": "https://explore.skillbuilder.aws/learn",            "type": "Course",   "duration": "10 hrs"},
    ],
    "docker": [
        {"title": "Docker Full Course – TechWorld with Nana",   "url": "https://www.youtube.com/watch?v=3c-iBn73dDE",      "type": "Video",    "duration": "5 hrs"},
        {"title": "Docker Official Get Started",                "url": "https://docs.docker.com/get-started/",              "type": "Article",  "duration": "2 hrs"},
        {"title": "Docker Practice – Play With Docker",         "url": "https://labs.play-with-docker.com/",                "type": "Practice", "duration": "2 hrs"},
    ],
    "kubernetes": [
        {"title": "Kubernetes Full Course – TechWorld with Nana", "url": "https://www.youtube.com/watch?v=X48VuDVv0do",    "type": "Video",    "duration": "8 hrs"},
        {"title": "Kubernetes Official Tutorial",               "url": "https://kubernetes.io/docs/tutorials/",             "type": "Article",  "duration": "3 hrs"},
    ],
    "linux": [
        {"title": "Linux Command Line – freeCodeCamp",          "url": "https://www.youtube.com/watch?v=iwolPf6kN-k",      "type": "Video",    "duration": "5 hrs"},
        {"title": "Linux Journey – Interactive",                "url": "https://linuxjourney.com/",                         "type": "Course",   "duration": "6 hrs"},
    ],
    "git": [
        {"title": "Git & GitHub – freeCodeCamp",                "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",      "type": "Video",    "duration": "1 hr"},
        {"title": "Git Official Book",                          "url": "https://git-scm.com/book/en/v2",                    "type": "Article",  "duration": "3 hrs"},
        {"title": "Learn Git Branching – Interactive",          "url": "https://learngitbranching.js.org/",                 "type": "Practice", "duration": "2 hrs"},
    ],
    # ── AI / ML ─────────────────────────────────────────────────────────────
    "machine learning": [
        {"title": "Machine Learning – Andrew Ng (Coursera)",    "url": "https://www.coursera.org/specializations/machine-learning-introduction", "type": "Course", "duration": "33 hrs"},
        {"title": "ML Course – fast.ai",                        "url": "https://course.fast.ai/",                           "type": "Course",   "duration": "20 hrs"},
        {"title": "ML Practice – Kaggle",                       "url": "https://www.kaggle.com/learn",                      "type": "Practice", "duration": "5 hrs"},
    ],
    "deep learning": [
        {"title": "Deep Learning Specialization – Coursera",    "url": "https://www.coursera.org/specializations/deep-learning", "type": "Course", "duration": "80 hrs"},
        {"title": "Deep Learning – fast.ai",                    "url": "https://course.fast.ai/",                           "type": "Course",   "duration": "20 hrs"},
    ],
    "tensorflow": [
        {"title": "TensorFlow Full Course – freeCodeCamp",      "url": "https://www.youtube.com/watch?v=tPYj3fFJGjk",      "type": "Video",    "duration": "7 hrs"},
        {"title": "TensorFlow Official Tutorials",              "url": "https://www.tensorflow.org/tutorials",              "type": "Article",  "duration": "4 hrs"},
    ],
    "pytorch": [
        {"title": "PyTorch Full Course – freeCodeCamp",         "url": "https://www.youtube.com/watch?v=Z_ikDlimN6A",      "type": "Video",    "duration": "10 hrs"},
        {"title": "PyTorch Official Tutorials",                 "url": "https://pytorch.org/tutorials/",                    "type": "Article",  "duration": "4 hrs"},
    ],
    # ── Data Science ────────────────────────────────────────────────────────
    "pandas": [
        {"title": "Pandas Full Course – freeCodeCamp",          "url": "https://www.youtube.com/watch?v=gtjxAH8uaP0",      "type": "Video",    "duration": "4 hrs"},
        {"title": "Pandas Official Getting Started",            "url": "https://pandas.pydata.org/docs/getting_started/intro_tutorials/", "type": "Article", "duration": "2 hrs"},
        {"title": "Pandas Practice – Kaggle",                   "url": "https://www.kaggle.com/learn/pandas",               "type": "Practice", "duration": "4 hrs"},
    ],
    "numpy": [
        {"title": "NumPy Full Course – freeCodeCamp",           "url": "https://www.youtube.com/watch?v=QUT1VHiLmmI",      "type": "Video",    "duration": "1 hr"},
        {"title": "NumPy Official Quickstart",                  "url": "https://numpy.org/doc/stable/user/quickstart.html", "type": "Article",  "duration": "1 hr"},
    ],
    # ── System Design ───────────────────────────────────────────────────────
    "system design": [
        {"title": "System Design Primer – GitHub",              "url": "https://github.com/donnemartin/system-design-primer", "type": "Article", "duration": "10 hrs"},
        {"title": "System Design Interview – Gaurav Sen",       "url": "https://www.youtube.com/watch?v=xpDnVSmNFX0",      "type": "Video",    "duration": "3 hrs"},
        {"title": "Grokking System Design – Educative",         "url": "https://www.educative.io/courses/grokking-the-system-design-interview", "type": "Course", "duration": "15 hrs"},
    ],
    # ── OOP ─────────────────────────────────────────────────────────────────
    "oop": [
        {"title": "OOP in Python – Corey Schafer",              "url": "https://www.youtube.com/watch?v=ZDa-Z5JzLYM",      "type": "Video",    "duration": "2 hrs"},
        {"title": "OOP Concepts – GeeksforGeeks",               "url": "https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/", "type": "Article", "duration": "2 hrs"},
    ],
    # ── REST APIs ───────────────────────────────────────────────────────────
    "rest apis": [
        {"title": "REST API Design – freeCodeCamp",             "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",      "type": "Video",    "duration": "5 hrs"},
        {"title": "REST API Tutorial",                          "url": "https://restfulapi.net/",                           "type": "Article",  "duration": "2 hrs"},
    ],
    # ── Redis ───────────────────────────────────────────────────────────────
    "redis": [
        {"title": "Redis Crash Course – Traversy Media",        "url": "https://www.youtube.com/watch?v=jgpVdJB2sKQ",      "type": "Video",    "duration": "1.5 hrs"},
        {"title": "Redis University – Free",                    "url": "https://university.redis.com/",                     "type": "Course",   "duration": "4 hrs"},
    ],
    # ── Kafka ───────────────────────────────────────────────────────────────
    "kafka": [
        {"title": "Apache Kafka Full Course – freeCodeCamp",    "url": "https://www.youtube.com/watch?v=ut5kNzMREg8",      "type": "Video",    "duration": "4 hrs"},
        {"title": "Kafka Official Quickstart",                  "url": "https://kafka.apache.org/quickstart",               "type": "Article",  "duration": "1 hr"},
    ],
    # ── C++ ─────────────────────────────────────────────────────────────────
    "c++": [
        {"title": "C++ Full Course – freeCodeCamp",             "url": "https://www.youtube.com/watch?v=8jLOx1hD3_o",      "type": "Video",    "duration": "10 hrs"},
        {"title": "C++ Tutorial – W3Schools",                   "url": "https://www.w3schools.com/cpp/",                    "type": "Article",  "duration": "3 hrs"},
        {"title": "C++ Practice – HackerRank",                  "url": "https://www.hackerrank.com/domains/cpp",            "type": "Practice", "duration": "3 hrs"},
    ],
    # ── Tailwind ────────────────────────────────────────────────────────────
    "tailwind": [
        {"title": "Tailwind CSS Full Course – freeCodeCamp",    "url": "https://www.youtube.com/watch?v=lCxcTsOHrjo",      "type": "Video",    "duration": "4 hrs"},
        {"title": "Tailwind CSS Official Docs",                 "url": "https://tailwindcss.com/docs/installation",         "type": "Article",  "duration": "2 hrs"},
    ],
    # ── Firebase ────────────────────────────────────────────────────────────
    "firebase": [
        {"title": "Firebase Full Course – freeCodeCamp",        "url": "https://www.youtube.com/watch?v=fgdpvwEWJ9M",      "type": "Video",    "duration": "6 hrs"},
        {"title": "Firebase Official Docs",                     "url": "https://firebase.google.com/docs/guides",           "type": "Article",  "duration": "2 hrs"},
    ],
    # ── Go ──────────────────────────────────────────────────────────────────
    "go": [
        {"title": "Go Full Course – freeCodeCamp",              "url": "https://www.youtube.com/watch?v=un6ZyFkqFKo",      "type": "Video",    "duration": "7 hrs"},
        {"title": "Go Official Tour",                           "url": "https://go.dev/tour/welcome/1",                     "type": "Practice", "duration": "3 hrs"},
    ],
    # ── Kotlin ──────────────────────────────────────────────────────────────
    "kotlin": [
        {"title": "Kotlin Full Course – freeCodeCamp",          "url": "https://www.youtube.com/watch?v=F9UC9DY-vIU",      "type": "Video",    "duration": "4 hrs"},
        {"title": "Kotlin Official Docs",                       "url": "https://kotlinlang.org/docs/getting-started.html",  "type": "Article",  "duration": "2 hrs"},
    ],
    # ── Scala ───────────────────────────────────────────────────────────────
    "scala": [
        {"title": "Scala Full Course – Alvin Alexander",        "url": "https://www.youtube.com/watch?v=-8V6bMjThNo",      "type": "Video",    "duration": "3 hrs"},
        {"title": "Scala Official Tour",                        "url": "https://docs.scala-lang.org/tour/tour-of-scala.html", "type": "Article", "duration": "2 hrs"},
    ],
    # ── Power BI / Excel ────────────────────────────────────────────────────
    "power bi": [
        {"title": "Power BI Full Course – freeCodeCamp",        "url": "https://www.youtube.com/watch?v=NNSHu0rkew8",      "type": "Video",    "duration": "10 hrs"},
        {"title": "Power BI Microsoft Learn",                   "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", "type": "Course", "duration": "8 hrs"},
    ],
    "excel": [
        {"title": "Excel Full Course – freeCodeCamp",           "url": "https://www.youtube.com/watch?v=Vl0H-qTclOg",      "type": "Video",    "duration": "4 hrs"},
        {"title": "Excel Practice – Excel Exercises",           "url": "https://excelexercises.com/",                       "type": "Practice", "duration": "3 hrs"},
    ],
}

# Fallback resources when skill not in DB
_FALLBACK_RESOURCES = [
    {"title": "Search on YouTube",                              "url": "https://www.youtube.com/results?search_query=",    "type": "Video",    "duration": "varies"},
    {"title": "GeeksforGeeks – Computer Science",               "url": "https://www.geeksforgeeks.org/",                    "type": "Article",  "duration": "varies"},
    {"title": "LeetCode Practice",                              "url": "https://leetcode.com/problemset/",                  "type": "Practice", "duration": "varies"},
]


def _get_resources_for_skill(skill: str) -> List[Dict[str, Any]]:
    """Match skill to curated DB. Fuzzy match on lowercase keywords."""
    skill_lower = skill.lower().strip()

    # Exact match first
    if skill_lower in _RESOURCE_DB:
        return [{"skill": skill, **r} for r in _RESOURCE_DB[skill_lower]]

    # Partial match — skill contains key or key contains skill
    for key, resources in _RESOURCE_DB.items():
        if key in skill_lower or skill_lower in key:
            return [{"skill": skill, **r} for r in resources]

    # Keyword match — any word in skill matches a DB key
    words = skill_lower.split()
    for word in words:
        if word in _RESOURCE_DB:
            return [{"skill": skill, **r} for r in _RESOURCE_DB[word]]

    # Fallback
    return [{"skill": skill, **r} for r in _FALLBACK_RESOURCES[:2]]


def build_curated_resources(missing_skills: List[str]) -> List[Dict[str, Any]]:
    """Build verified resource list for all missing skills (max 3 per skill)."""
    resources = []
    for skill in missing_skills:
        skill_resources = _get_resources_for_skill(skill)
        resources.extend(skill_resources[:3])
    return resources


# ─── Duration Estimator ───────────────────────────────────────────────────────

def estimate_duration_weeks(missing_skills: List[str], hours_per_day: float, level: str) -> int:
    base_hours = {"beginner": 8, "intermediate": 5, "advanced": 3}
    hours_per_skill = base_hours.get(level, 6)
    total_hours = len(missing_skills) * hours_per_skill
    weeks = math.ceil(total_hours / (hours_per_day * 7))
    return max(2, min(weeks, 24))


# ─── Roadmap Plan Generation via Groq ────────────────────────────────────────
# NOTE: Groq only generates plans (daily/weekly/milestones/mock_interviews).
# Resources are built from our curated DB — NOT from Groq (avoids hallucinated URLs).

_ROADMAP_PROMPT = """Create a learning roadmap. Return ONLY valid JSON.

Student: {level} level, wants to be {target_role}
Missing Skills: {missing_skills}
Hours/day: {hours_per_day} | Duration: {duration_weeks} weeks

{{"daily_plan":[{{"day":1,"topic":"skill","tasks":["task1","task2"],"duration_hours":{hours_per_day}}}],
"weekly_plan":[{{"week":1,"focus":"skill","goals":["goal1","goal2"],"deliverable":"what to build","skills_covered":["skill1"]}}],
"monthly_milestones":[{{"month":1,"milestone":"achievement","assessment":"how to test","skills_mastered":["skill1"]}}],
"mock_interview_schedule":[{{"week":4,"type":"Technical Coding","topics":["skill1"],"duration_minutes":60,"platform":"LeetCode"}}]}}

Rules: daily_plan=14 days only, weekly_plan=all {duration_weeks} weeks, tasks must be specific."""


def generate_plan_with_groq(
    missing_skills: List[str],
    student_level: str,
    available_hours_per_day: float,
    target_role: str,
    duration_weeks: int,
) -> dict:
    prompt = _ROADMAP_PROMPT.format(
        level=student_level,
        target_role=target_role,
        missing_skills=", ".join(missing_skills[:10]),  # cap at 10 skills
        hours_per_day=available_hours_per_day,
        duration_weeks=duration_weeks,
    )
    return _parse_json(_groq(prompt))


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def generate_roadmap(
    missing_skills: List[str],
    student_level: str,
    available_hours_per_day: float,
    target_role: str,
) -> dict:
    duration_weeks = estimate_duration_weeks(missing_skills, available_hours_per_day, student_level)

    if not missing_skills:
        return {
            "target_role": target_role,
            "duration_weeks": 2,
            "daily_plan": [],
            "weekly_plan": [{"week": 1, "focus": "Interview Prep", "goals": ["Revise core concepts", "Solve 10 LeetCode problems", "Mock interviews"], "deliverable": "Ready for placement", "skills_covered": []}],
            "monthly_milestones": [{"month": 1, "milestone": "Placement Ready", "assessment": "Complete 2 mock interviews", "skills_mastered": []}],
            "resources": [
                {"skill": "Interview Prep", "title": "LeetCode Top 150 Problems", "url": "https://leetcode.com/studyplan/top-interview-150/", "type": "Practice", "duration": "20 hrs"},
                {"skill": "Interview Prep", "title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "Article", "duration": "10 hrs"},
            ],
            "mock_interview_schedule": [{"week": 1, "type": "Full Mock Interview", "topics": ["DSA", "System Design"], "duration_minutes": 60, "platform": "Pramp"}],
        }

    # Generate plan from Groq (no URLs)
    plan = generate_plan_with_groq(missing_skills, student_level, available_hours_per_day, target_role, duration_weeks)

    # Build resources from curated DB (verified URLs)
    resources = build_curated_resources(missing_skills)

    plan["target_role"]    = target_role
    plan["duration_weeks"] = duration_weeks
    plan["resources"]      = resources   # overwrite any Groq-generated resources

    return plan
