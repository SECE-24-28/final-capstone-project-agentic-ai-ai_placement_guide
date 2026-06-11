"""
Agent 2: Skill Gap Analyzer
Responsibilities: Compare skills vs target role → missing skills → gap % → learning order
"""
import re
import json
from typing import List

from groq import Groq
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.core.config import settings
from app.core.embedder import embedder as _embedder

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
                messages=[{"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON only."}, {"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
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


# ─── Role Requirements via Groq ───────────────────────────────────────────────

_ROLE_SKILLS_PROMPT = """List skills required for: "{target_role}". Return ONLY JSON:
{{"required_skills":["skill1","skill2"],"core_skills":["must1"],"nice_to_have":["opt1"]}}
Include 12-18 skills total (languages, frameworks, tools, databases, concepts)."""

def get_role_requirements(target_role: str) -> dict:
    return _parse_json(_groq(_ROLE_SKILLS_PROMPT.format(target_role=target_role)))


# ─── Semantic Skill Matching ──────────────────────────────────────────────────

def semantic_match(candidate_skills: List[str], required_skills: List[str], threshold: float = 0.75) -> tuple:
    if not candidate_skills or not required_skills:
        return [], required_skills

    cand_embeddings = _embedder.encode(candidate_skills)
    req_embeddings = _embedder.encode(required_skills)
    similarity_matrix = cosine_similarity(cand_embeddings, req_embeddings)

    matched = set()
    missing = []
    for j, req_skill in enumerate(required_skills):
        if np.max(similarity_matrix[:, j]) >= threshold:
            matched.add(req_skill)
        else:
            missing.append(req_skill)

    return list(matched), missing


# ─── Priority Ranking via Groq ────────────────────────────────────────────────

_PRIORITY_PROMPT = """Rank these missing skills for "{target_role}" by priority. Return ONLY JSON:
{{"priority_skills":["highest first"],"recommended_learning_order":["learn this first"],"rationale":"brief"}}
Missing: {missing_skills}"""

def prioritize_skills(missing_skills: List[str], target_role: str) -> dict:
    if not missing_skills:
        return {"priority_skills": [], "recommended_learning_order": [], "rationale": "No missing skills"}
    prompt = _PRIORITY_PROMPT.format(target_role=target_role, missing_skills=", ".join(missing_skills[:15]))
    return _parse_json(_groq(prompt))


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def analyze_skill_gap(skills: List[str], target_role: str) -> dict:
    role_data = get_role_requirements(target_role)
    required_skills = role_data.get("required_skills", [])

    matched_skills, missing_skills = semantic_match(skills, required_skills)

    gap_percentage = round((len(missing_skills) / len(required_skills)) * 100, 1) if required_skills else 0.0

    priority_data = prioritize_skills(missing_skills, target_role)

    return {
        "target_role": target_role,
        "skill_gap_percentage": gap_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "priority_skills": priority_data.get("priority_skills", missing_skills),
        "recommended_learning_order": priority_data.get("recommended_learning_order", missing_skills),
        "all_required_skills": required_skills,
    }
