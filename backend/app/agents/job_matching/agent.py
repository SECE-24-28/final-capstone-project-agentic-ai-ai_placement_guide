"""
Agent 4: Job Matching Agent — Fixed & Improved

Fixes applied:
  1. Resume scorer defined    — section completeness + keyword density vs JD
  2. Weight normalization     — None scores are excluded; remaining weights re-normalized to 1.0
  3. CGPA negative clamp      — max(0, ...) applied
  4. Configurable threshold   — SKILL_MATCH_THRESHOLD + soft-match partial credit fallback
  5. Unknown batch year       — returns None (excluded) instead of 50 (unfair credit)
  6. Fuzzy cert matching      — rapidfuzz token_set_ratio >= 85, exact match fallback
"""
import re
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.embedder import embedder as _embedder

# Fix 4: configurable threshold — change this one constant to tune all skill matching
SKILL_MATCH_THRESHOLD = 0.72


# ─── Fix 1: Resume Scorer ─────────────────────────────────────────────────────

_RESUME_SECTIONS = [
    r"\b(summary|objective|profile|about)\b",
    r"\b(skills|technologies|competencies)\b",
    r"\b(experience|internship|employment)\b",
    r"\b(education|degree|university|college)\b",
    r"\b(certifications?|certificates?|courses?)\b",
]


def _resume_score(resume_raw_text: str, job_required_skills: List[str]) -> float:
    """
    Fix 1: Resume score = 60% section completeness + 40% keyword density vs JD.
    Defined here instead of blindly passing the ATS score from Agent 1,
    so the job matcher has a self-contained quality signal per job posting.
    """
    if not resume_raw_text:
        return 0.0

    text_lower = resume_raw_text.lower()

    # Section completeness (60 pts)
    sections_found = sum(1 for p in _RESUME_SECTIONS if re.search(p, text_lower))
    section_score = (sections_found / len(_RESUME_SECTIONS)) * 100

    # Keyword density vs this specific job's required skills (40 pts)
    if job_required_skills:
        matched = sum(1 for s in job_required_skills if s.lower() in text_lower)
        keyword_score = (matched / len(job_required_skills)) * 100
    else:
        keyword_score = 100.0  # no requirements → no penalty

    return round(section_score * 0.60 + keyword_score * 0.40, 1)


# ─── Fix 4 + Soft-match: Skill Scorer ────────────────────────────────────────

def _skill_score(
    candidate_skills: List[str],
    required_skills: List[str],
) -> Tuple[float, List[str]]:
    """
    Fix 4a: Uses SKILL_MATCH_THRESHOLD (configurable) instead of hardcoded 0.72.
    Fix 4b: Soft-match fallback — if no hard match, best_cosine × 0.5 as partial credit.
    """
    if not required_skills:
        return 100.0, []
    if not candidate_skills:
        return 0.0, list(required_skills)

    cand_emb = _embedder.encode([s.lower() for s in candidate_skills])
    req_emb  = _embedder.encode([s.lower() for s in required_skills])
    sim_matrix = cosine_similarity(cand_emb, req_emb)  # (n_cand, n_req)

    total_score = 0.0
    missing = []

    for j, req in enumerate(required_skills):
        best_sim = float(np.max(sim_matrix[:, j]))

        if best_sim >= SKILL_MATCH_THRESHOLD:
            # Hard match: full credit
            total_score += 1.0
        else:
            # Fix 4b: soft-match partial credit instead of 0
            total_score += best_sim * 0.5
            missing.append(req)

    score = round((total_score / len(required_skills)) * 100, 1)
    return score, missing


# ─── Fix 3: CGPA Scorer ───────────────────────────────────────────────────────

def _cgpa_score(candidate_cgpa: Optional[float], min_cgpa: Optional[float]) -> Optional[float]:
    """
    Fix 3: Clamp to max(0, ...) so deficit larger than min_cgpa can't go negative.
    Returns None if criterion not present in job → excluded from weights.
    """
    if candidate_cgpa is None or min_cgpa is None:
        return None
    if candidate_cgpa >= min_cgpa:
        return 100.0
    deficit = min_cgpa - candidate_cgpa
    # Fix 3: was missing max(0, ...) — deficit > min_cgpa gave negative score
    return max(0.0, round((1 - deficit / min_cgpa) * 100, 1))


# ─── Experience Scorer ────────────────────────────────────────────────────────

def _experience_score(
    candidate_months: Optional[int],
    required_months: Optional[int],
) -> Optional[float]:
    """Returns None when job has no experience requirement → excluded from weights."""
    if required_months is None or required_months == 0:
        return None
    if candidate_months is None or candidate_months == 0:
        return 0.0
    return min(100.0, round((candidate_months / required_months) * 100, 1))


# ─── Fix 6: Certification Scorer ─────────────────────────────────────────────

def _certification_score(
    candidate_certs: List[str],
    required_certs: Optional[List[str]],
) -> Optional[float]:
    """
    Fix 6: Fuzzy match via rapidfuzz token_set_ratio >= 85.
    Falls back to exact lowercase match if rapidfuzz is unavailable.
    Returns None if job has no cert requirement → excluded from weights.
    """
    if not required_certs:
        return None
    if not candidate_certs:
        return 0.0

    try:
        from rapidfuzz import fuzz
        def _is_match(req: str, cands: List[str]) -> bool:
            return any(fuzz.token_set_ratio(req.lower(), c.lower()) >= 85 for c in cands)
    except ImportError:
        # Fallback: exact lowercase match
        def _is_match(req: str, cands: List[str]) -> bool:
            return req.lower() in {c.lower() for c in cands}

    matched = sum(1 for r in required_certs if _is_match(r, candidate_certs))
    return round((matched / len(required_certs)) * 100, 1)


# ─── Fix 5: Batch Scorer ─────────────────────────────────────────────────────

def _batch_score(
    candidate_year: Optional[int],
    batch_years: Optional[List[int]],
) -> Optional[float]:
    """
    Fix 5: Unknown graduation year now returns None (excluded from scoring)
    instead of 50 (which gave unfair partial credit for missing data).
    Returns None when job has no batch filter too.
    """
    if not batch_years:
        return None
    if candidate_year is None:
        # Fix 5: was returning 50 — now excluded entirely
        return None
    return 100.0 if candidate_year in batch_years else 0.0


# ─── Fix 2: Dynamic Weight Engine with Re-normalization ──────────────────────

def calculate_dynamic_score(
    candidate_skills: List[str],
    resume_raw_text: str,
    candidate_cgpa: Optional[float],
    candidate_graduation_year: Optional[int],
    candidate_experience_months: Optional[int],
    candidate_certifications: List[str],
    job: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fix 2: Weight re-normalization.
    After computing all scores, any criterion that returned None is dropped.
    The remaining raw weights are re-normalized so they always sum to exactly 1.0.

    Base raw weights (before normalization):
      skill: 0.50, resume: 0.20, cgpa: 0.15, experience: 0.15, certs: 0.10, batch: 0.10
    """
    required_skills = job.get("required_skills", [])

    # Compute all scores
    skill_sc = _skill_score(candidate_skills, required_skills)
    score_val, missing = skill_sc

    all_scores: Dict[str, Optional[float]] = {
        "skill_score":         score_val,
        "resume_score":        _resume_score(resume_raw_text, required_skills),
        "cgpa_score":          _cgpa_score(candidate_cgpa, job.get("min_cgpa")),
        "experience_score":    _experience_score(candidate_experience_months, job.get("min_experience_months")),
        "certification_score": _certification_score(candidate_certifications, job.get("required_certifications")),
        "batch_score":         _batch_score(candidate_graduation_year, job.get("batch_years")),
    }

    # Raw weights — skill and resume are always present
    raw_weights: Dict[str, float] = {
        "skill_score":         0.50,
        "resume_score":        0.20,
        "cgpa_score":          0.15,
        "experience_score":    0.15,
        "certification_score": 0.10,
        "batch_score":         0.10,
    }

    # Fix 2: Drop criteria with None scores and re-normalize remaining weights
    active = {k: v for k, v in all_scores.items() if v is not None}
    active_raw = {k: raw_weights[k] for k in active}
    total_raw = sum(active_raw.values())

    # Normalize so weights sum to exactly 1.0
    normalized_weights = {k: round(w / total_raw, 4) for k, w in active_raw.items()}

    final_score = round(sum(active[k] * normalized_weights[k] for k in active), 1)

    return {
        "final_score": final_score,
        "score_breakdown": {
            **active,
            "weights_used":  {k: round(normalized_weights[k] * 100) for k in normalized_weights},
            "criteria_used": list(active.keys()),
        },
        "missing_skills": missing,
    }


# ─── Placement Prediction ─────────────────────────────────────────────────────

def predict_placement(score: float) -> str:
    if score >= 80: return "Highly Likely"
    if score >= 65: return "Likely"
    if score >= 50: return "Possible"
    if score >= 35: return "Unlikely"
    return "Not Ready"


# ─── Main Agent Entry Point ───────────────────────────────────────────────────

async def match_jobs(
    skills: List[str],
    resume_score: float,
    resume_raw_text: str,
    cgpa: Optional[float],
    graduation_year: Optional[int],
    experience_months: Optional[int],
    certifications: List[str],
    jobs: List[Dict[str, Any]],
) -> dict:
    results = []

    for job in jobs:
        scored = calculate_dynamic_score(
            candidate_skills=skills,
            resume_raw_text=resume_raw_text,
            candidate_cgpa=cgpa,
            candidate_graduation_year=graduation_year,
            candidate_experience_months=experience_months,
            candidate_certifications=certifications,
            job=job,
        )
        results.append({
            "job_id":               job["id"],
            "company":              job["company"],
            "role":                 job["role"],
            "job_type":             job.get("job_type", "A"),
            "match_score":          scored["final_score"],
            "score_breakdown":      scored["score_breakdown"],
            "missing_skills":       scored["missing_skills"],
            "placement_prediction": predict_placement(scored["final_score"]),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)

    # Best match per company
    seen: Dict[str, dict] = {}
    for r in results:
        c = r["company"]
        if c not in seen or r["match_score"] > seen[c]["match_score"]:
            seen[c] = {"company": c, "best_role": r["role"], "match_score": r["match_score"]}
    company_rankings = sorted(seen.values(), key=lambda x: x["match_score"], reverse=True)

    top_score = results[0]["match_score"] if results else 0.0

    return {
        "job_matches":          results[:10],
        "company_rankings":     company_rankings[:10],
        "match_probability":    top_score,
        "placement_prediction": predict_placement(top_score),
        "total_jobs_analyzed":  len(jobs),
    }
