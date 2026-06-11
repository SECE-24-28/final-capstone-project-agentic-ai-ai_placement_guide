"""
Agent 4: Job Matching Agent
Dynamic scoring: auto-detects available criteria per job and weights accordingly.
No fixed formula — weights are normalized based on what each job posting provides.
"""
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_embedder = SentenceTransformer("all-MiniLM-L6-v2")


# ─── Dynamic Scoring Engine ───────────────────────────────────────────────────

def _skill_score(candidate_skills: List[str], required_skills: List[str]) -> tuple[float, List[str]]:
    """Semantic skill matching using embeddings."""
    if not required_skills:
        return 100.0, []
    if not candidate_skills:
        return 0.0, required_skills

    cand_emb = _embedder.encode([s.lower() for s in candidate_skills])
    req_emb = _embedder.encode([s.lower() for s in required_skills])
    sim_matrix = cosine_similarity(cand_emb, req_emb)

    matched_count = 0
    missing = []
    for j, req in enumerate(required_skills):
        if np.max(sim_matrix[:, j]) >= 0.72:
            matched_count += 1
        else:
            missing.append(req)

    return round((matched_count / len(required_skills)) * 100, 1), missing


def _cgpa_score(candidate_cgpa: Optional[float], min_cgpa: Optional[float]) -> float:
    if candidate_cgpa is None or min_cgpa is None:
        return None
    if candidate_cgpa >= min_cgpa:
        return 100.0
    deficit = min_cgpa - candidate_cgpa
    return max(0.0, round((1 - deficit / min_cgpa) * 100, 1))


def _experience_score(candidate_months: Optional[int], required_months: Optional[int]) -> float:
    if required_months is None or required_months == 0:
        return None
    if candidate_months is None:
        return 0.0
    if candidate_months >= required_months:
        return 100.0
    return round((candidate_months / required_months) * 100, 1)


def _certification_score(candidate_certs: List[str], required_certs: Optional[List[str]]) -> float:
    if not required_certs:
        return None
    if not candidate_certs:
        return 0.0
    candidate_lower = {c.lower() for c in candidate_certs}
    matched = sum(1 for c in required_certs if c.lower() in candidate_lower)
    return round((matched / len(required_certs)) * 100, 1)


def _degree_score(candidate_graduation_year: Optional[int], batch_years: Optional[List[int]]) -> float:
    if not batch_years:
        return None
    if candidate_graduation_year is None:
        return 50.0
    return 100.0 if candidate_graduation_year in batch_years else 0.0


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
    Dynamically weights scoring based on criteria present in the job posting.
    Each criterion gets a weight only if it exists in the job posting.
    resume_score is always included as a base quality signal.
    """
    scores = {}
    weights = {}

    # Always score skills (primary criterion)
    skill_sc, missing = _skill_score(candidate_skills, job.get("required_skills", []))
    scores["skill_score"] = skill_sc
    weights["skill_score"] = 0.50

    # Always include resume quality as baseline
    scores["resume_score"] = resume_score
    weights["resume_score"] = 0.20

    remaining_weight = 0.30
    optional_criteria = []

    cgpa_sc = _cgpa_score(candidate_cgpa, job.get("min_cgpa"))
    if cgpa_sc is not None:
        optional_criteria.append(("cgpa_score", cgpa_sc))

    exp_sc = _experience_score(candidate_experience_months, job.get("min_experience_months"))
    if exp_sc is not None:
        optional_criteria.append(("experience_score", exp_sc))

    cert_sc = _certification_score(candidate_certifications, job.get("required_certifications"))
    if cert_sc is not None:
        optional_criteria.append(("certification_score", cert_sc))

    batch_sc = _degree_score(candidate_graduation_year, job.get("batch_years"))
    if batch_sc is not None:
        optional_criteria.append(("batch_score", batch_sc))

    # Distribute remaining 30% equally among available optional criteria
    if optional_criteria:
        per_criterion = remaining_weight / len(optional_criteria)
        for name, val in optional_criteria:
            scores[name] = val
            weights[name] = per_criterion

    # Weighted average
    final_score = sum(scores[k] * weights[k] for k in scores)

    return {
        "final_score": round(final_score, 1),
        "score_breakdown": {**scores, "criteria_used": list(scores.keys())},
        "missing_skills": missing,
    }


# ─── Placement Prediction ─────────────────────────────────────────────────────

def predict_placement(match_score: float) -> str:
    if match_score >= 80:
        return "Highly Likely"
    elif match_score >= 65:
        return "Likely"
    elif match_score >= 50:
        return "Possible"
    elif match_score >= 35:
        return "Unlikely"
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
            skills, resume_score, cgpa, graduation_year,
            experience_months, certifications, job
        )
        results.append({
            "job_id": job["id"],
            "company": job["company"],
            "role": job["role"],
            "match_score": scored["final_score"],
            "score_breakdown": scored["score_breakdown"],
            "missing_skills": scored["missing_skills"],
            "placement_prediction": predict_placement(scored["final_score"]),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)

    # Company rankings: best job per company
    company_seen = {}
    for r in results:
        c = r["company"]
        if c not in company_seen or r["match_score"] > company_seen[c]["match_score"]:
            company_seen[c] = {"company": c, "best_role": r["role"], "match_score": r["match_score"]}
    company_rankings = sorted(company_seen.values(), key=lambda x: x["match_score"], reverse=True)

    top_score = results[0]["match_score"] if results else 0.0

    return {
        "job_matches": results[:10],
        "company_rankings": company_rankings[:10],
        "match_probability": top_score,
        "placement_prediction": predict_placement(top_score),
        "total_jobs_analyzed": len(jobs),
    }
