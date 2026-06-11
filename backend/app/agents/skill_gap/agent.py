"""
Agent 2: Skill Gap Analyzer
Responsibilities: Compare skills vs target role → missing skills → gap % → learning order
"""
import re
import json
from typing import List

from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.core.config import settings

_client = Groq(api_key=settings.GROQ_API_KEY)
_embedder = SentenceTransformer("all-MiniLM-L6-v2")


def _groq(prompt: str) -> str:
    response = _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ─── Role Requirements via Groq ───────────────────────────────────────────────

_ROLE_SKILLS_PROMPT = """You are a technical recruiter expert. List ALL skills required for the role: "{target_role}".

Return ONLY valid JSON:
{{
  "required_skills": ["skill1", "skill2", ...],
  "core_skills": ["must-have skill1", "must-have skill2"],
  "nice_to_have": ["optional skill1", "optional skill2"]
}}

Include: programming languages, frameworks, tools, databases, concepts, soft skills.
Return 15-25 required skills total."""

def get_role_requirements(target_role: str) -> dict:
    prompt = _ROLE_SKILLS_PROMPT.format(target_role=target_role)
    return _parse_json(_groq(prompt))


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

_PRIORITY_PROMPT = """You are a career coach. Given these missing skills for "{target_role}", rank them by priority.

Missing skills: {missing_skills}

Return ONLY valid JSON:
{{
  "priority_skills": ["highest priority skill first", ...],
  "recommended_learning_order": ["learn this first", "then this", ...],
  "rationale": "brief explanation"
}}

Consider: job market demand, prerequisite dependencies, learning difficulty."""

def prioritize_skills(missing_skills: List[str], target_role: str) -> dict:
    if not missing_skills:
        return {"priority_skills": [], "recommended_learning_order": [], "rationale": "No missing skills"}

    prompt = _PRIORITY_PROMPT.format(
        target_role=target_role,
        missing_skills=", ".join(missing_skills)
    )
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
