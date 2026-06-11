"""
Agent 3: Roadmap Generator
Responsibilities: Personalized learning roadmap → daily/weekly/monthly plans → resources → mock interviews
"""
import re
import json
import math
from typing import List

from groq import Groq

from app.core.config import settings

_client = Groq(api_key=settings.GROQ_API_KEY)


def _groq(prompt: str) -> str:
    response = _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=8192,
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ─── Duration Estimator ───────────────────────────────────────────────────────

def estimate_duration_weeks(missing_skills: List[str], hours_per_day: float, level: str) -> int:
    base_hours = {"beginner": 8, "intermediate": 5, "advanced": 3}
    hours_per_skill = base_hours.get(level, 6)
    total_hours = len(missing_skills) * hours_per_skill
    weeks = math.ceil(total_hours / (hours_per_day * 7))
    return max(2, min(weeks, 24))


# ─── Roadmap Generation via Groq ─────────────────────────────────────────────

_ROADMAP_PROMPT = """You are an expert career coach and curriculum designer.

Create a detailed, actionable learning roadmap for a {level} student who wants to become a {target_role}.

Student Profile:
- Missing Skills: {missing_skills}
- Available Hours Per Day: {hours_per_day}
- Duration: {duration_weeks} weeks

Return ONLY valid JSON with this exact structure:
{{
  "daily_plan": [
    {{"day": 1, "topic": "skill name", "tasks": ["task 1", "task 2"], "duration_hours": 2.0}},
    {{"day": 2, "topic": "skill name", "tasks": ["task 1", "task 2"], "duration_hours": 2.0}}
  ],
  "weekly_plan": [
    {{"week": 1, "focus": "main skill", "goals": ["goal 1", "goal 2"], "deliverable": "what to build/complete", "skills_covered": ["skill1"]}}
  ],
  "monthly_milestones": [
    {{"month": 1, "milestone": "What to achieve", "assessment": "How to test knowledge", "skills_mastered": ["skill1"]}}
  ],
  "resources": [
    {{"skill": "skill name", "title": "Resource Title", "url": "https://real-url.com", "type": "Video/Article/Course/Practice", "duration": "X hours"}}
  ],
  "mock_interview_schedule": [
    {{"week": 4, "type": "Technical Coding", "topics": ["DSA", "Python"], "duration_minutes": 60, "platform": "LeetCode"}}
  ]
}}

Rules:
- daily_plan: first 14 days only
- weekly_plan: all {duration_weeks} weeks
- resources: 2-3 per skill, use real URLs from Coursera/YouTube/freeCodeCamp/LeetCode/GeeksforGeeks
- Return ONLY the JSON, no other text"""

def generate_roadmap_with_groq(
    missing_skills: List[str],
    student_level: str,
    available_hours_per_day: float,
    target_role: str,
    duration_weeks: int,
) -> dict:
    prompt = _ROADMAP_PROMPT.format(
        level=student_level,
        target_role=target_role,
        missing_skills=", ".join(missing_skills),
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
            "weekly_plan": [{"week": 1, "focus": "Interview Prep", "goals": ["Revise core concepts", "Mock interviews"], "deliverable": "Ready for placement", "skills_covered": []}],
            "monthly_milestones": [{"month": 1, "milestone": "Placement Ready", "assessment": "Mock interviews", "skills_mastered": []}],
            "resources": [],
            "mock_interview_schedule": [{"week": 1, "type": "Full Mock Interview", "topics": ["All skills"], "duration_minutes": 60, "platform": "Pramp"}],
        }

    roadmap = generate_roadmap_with_groq(
        missing_skills, student_level, available_hours_per_day, target_role, duration_weeks
    )
    roadmap["target_role"] = target_role
    roadmap["duration_weeks"] = duration_weeks
    return roadmap
