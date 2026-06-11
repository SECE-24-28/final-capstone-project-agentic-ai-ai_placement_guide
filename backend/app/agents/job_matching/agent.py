"""
Agent 4: Job Matching Agent
Dynamic Scoring — weights auto-adjust based on criteria available in each job posting.

Job Type A → Skills(70%) + Resume(30%)
Job Type B → Skills(50%) + Resume(20%) + CGPA(30%)
Job Type C → Skills(50%) + Resume(20%) + Experience(30%)
Job Type D → Skills(40%) + Resume(20%) + CGPA(20%) + Batch(10%) + Certs(10%)

No fixed formula — engine detects available fields and normalizes weights automatically.
"""
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.core.embedder import embedder as _embedder


# ─── Individual Scorers ───────────────────────────────────────────────────────

def _skill_score(candidate_skills: List[str], required_skills: List[str]) -> Tuple[float, List[str]]:
    """
    Semantic skill matching via sentence-transformer embeddings.
    cosine similarity >= 0.72 → matched.
    Returns (score_0_to_100, missing_skills_list)
    """
    if not required_skills:
        return 100.0, []
    if not candidate_skills:
        return 0.0, list(required_skills)

    cand_emb = _embedder.encode([s.lower() for s in candidate_skills])
    req_emb  = _embedder.encode([s.lower() for s in required_skills])
    sim_matrix = cosine_similarity(cand_emb, req_emb)  # shape: (n_cand, n_req)

    matched, missing = 0, []
    for j, req in enumerate(required_skills):
        if float(np.max(sim_matrix[:, j])) >= 0.72:
            matched += 1
        else:
            missing.append(req)

    return round((matched / len(required_skills)) * 100, 1), missing


def _cgpa_score(candidate_cgpa: Optional[float], min_cgpa: Optional[float]) -> Optional[float]:
    """
    100  → candidate meets/exceeds requirement
    <100 → proportional penalty
    None → this criterion not present in job posting (skip)
    """
    if candidate_cgpa is None or min_cgpa is None:
        return None
    if candidate_cgpa >= min_cgpa:
        return 100.0
    deficit = min_cgpa - candidate_cgpa
    return max(0.0, round((1 - deficit / min_cgpa) * 100, 1))


def _experience_score(candidate_months: Optional[int], required_months: Optional[int]) -> Optional[float]:
    """
    None  → job has no experience requirement (skip)
    0 req → fresher ok → skip
    """
    if required_months is None or required_months == 0:
        return None
    if candidate_months is None or candidate_months == 0:
        return 0.0
    if candidate_months >= required_months:
        return 100.0
    return round((candidate_months / required_months) * 100, 1)


def _certification_score(candidate_certs: List[str], required_certs: Optional[List[str]]) -> Optional[float]:
    """None → job doesn't require certs (skip)"""
    if not required_certs:
        return None
    if not candidate_certs:
        return 0.0
    cand_lower = {c.lower() for c in candidate_certs}
    matched = sum(1 for c in required_certs if c.lower() in cand_lower)
    return round((matched / len(required_certs)) * 100, 1)


def _batch_score(candidate_year: Optional[int], batch_years: Optional[List[int]]) -> Optional[float]:
    """None → job has no batch filter (skip)"""
    if not batch_years:
        return None
    if candidate_year is None:
        return 50.0   # partial credit — unknown year
    return 100.0 if candidate_year in batch_years else 0.0


# ─── Dynamic Weight Engine ────────────────────────────────────────────────────

def calculate_dynamic_score(
    candidate_skills: List[str],
    resume_score: float,
    candidate_cgpa: Optional[float],
    candidate_graduation_year: Optional[int],
    candidate_experience_months: Optional[int],
    candidate_certifications: List[str],
    job: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Step 1 — Compute each individual score (None = criterion not in job).
    Step 2 — Build weight map: Skills gets highest base weight.
             Resume score is always included as quality baseline.
             Optional criteria share the remaining weight equally.
    Step 3 — Normalize weights to sum = 1.0.
    Step 4 — Weighted sum = final match score.

    Examples:
      Job A (Skills only)       → skill:0.70  resume:0.30
      Job B (Skills + CGPA)     → skill:0.50  resume:0.20  cgpa:0.30
      Job C (Skills + Exp)      → skill:0.50  resume:0.20  exp:0.30
      Job D (Skills+CGPA+Batch+Certs) → skill:0.40 resume:0.20 cgpa:0.15 batch:0.15 certs:0.10
    """
    skill_sc, missing = _skill_score(candidate_skills, job.get("required_skills", []))
    cgpa_sc   = _cgpa_score(candidate_cgpa, job.get("min_cgpa"))
    exp_sc    = _experience_score(candidate_experience_months, job.get("min_experience_months"))
    cert_sc   = _certification_score(candidate_certifications, job.get("required_certifications"))
    batch_sc  = _batch_score(candidate_graduation_year, job.get("batch_years"))

    # Collect present optional criteria
    optional: List[Tuple[str, float]] = []
    if cgpa_sc  is not None: optional.append(("cgpa_score",          cgpa_sc))
    if exp_sc   is not None: optional.append(("experience_score",    exp_sc))
    if cert_sc  is not None: optional.append(("certification_score", cert_sc))
    if batch_sc is not None: optional.append(("batch_score",         batch_sc))

    # Base weights
    SKILL_WEIGHT  = 0.50 if optional else 0.70
    RESUME_WEIGHT = 0.20 if optional else 0.30
    remaining     = round(1.0 - SKILL_WEIGHT - RESUME_WEIGHT, 4)

    scores  = {"skill_score": skill_sc, "resume_score": resume_score}
    weights = {"skill_score": SKILL_WEIGHT, "resume_score": RESUME_WEIGHT}

    if optional:
        per = round(remaining / len(optional), 4)
        for name, val in optional:
            scores[name]  = val
            weights[name] = per

    final_score = round(sum(scores[k] * weights[k] for k in scores), 1)

    return {
        "final_score": final_score,
        "score_breakdown": {
            **scores,
            "weights_used": {k: round(weights[k] * 100) for k in weights},
            "criteria_used": list(scores.keys()),
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
    cgpa: Optional[float],
    graduation_year: Optional[int],
    experience_months: Optional[int],
    certifications: List[str],
    jobs: List[Dict[str, Any]],
) -> dict:
    results = []

    for job in jobs:
        scored = calculate_dynamic_score(
            skills, resume_score, cgpa,
            graduation_year, experience_months, certifications, job,
        )
        results.append({
            "job_id":              job["id"],
            "company":             job["company"],
            "role":                job["role"],
            "job_type":            job.get("job_type", "A"),
            "match_score":         scored["final_score"],
            "score_breakdown":     scored["score_breakdown"],
            "missing_skills":      scored["missing_skills"],
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
        "job_matches":        results[:10],
        "company_rankings":   company_rankings[:10],
        "match_probability":  top_score,
        "placement_prediction": predict_placement(top_score),
        "total_jobs_analyzed": len(jobs),
    }
