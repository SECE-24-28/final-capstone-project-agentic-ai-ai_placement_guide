from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.core.security import get_current_user
from app.agents.job_matching.agent import match_jobs
from app.repositories.user_repo import StudentRepository
from app.repositories.resume_repo import ResumeRepository
from app.repositories.job_repo import JobRepository
from app.schemas.schemas import JobMatchRequest, JobMatchResponse, JobMatchResult, ScoreBreakdown
from app.core.embedder import embedder as _embedder
from app.services.features import (
    explain_match_score,
    rank_companies,
    analyze_skill_trends,
    get_jobs,
)


class ExplainRequest(BaseModel):
    score_breakdown: dict
    candidate_skills: List[str]
    job_required_skills: List[str]

router = APIRouter(prefix="/jobs", tags=["Job Matching"])


@router.post("/match", response_model=JobMatchResponse)
async def match_jobs_endpoint(payload: JobMatchRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    job_repo = JobRepository(db)
    if payload.target_role:
        query_emb = _embedder.encode(payload.target_role).tolist()
        jobs_list = await job_repo.semantic_search(query_emb, top_k=30)
        if len(jobs_list) < 5:
            jobs_list = await job_repo.get_all_active()
    else:
        jobs_list = await job_repo.get_all_active()

    jobs = [{"id": str(j["_id"]), "company": j["company"], "role": j["role"], "job_type": j.get("job_type", "A"), "required_skills": j.get("required_skills", []), "min_cgpa": j.get("min_cgpa"), "batch_years": j.get("batch_years"), "min_experience_months": j.get("min_experience_months", 0), "required_certifications": j.get("required_certifications")} for j in jobs_list]

    result = await match_jobs(skills=payload.skills, resume_score=payload.resume_score, resume_raw_text=payload.resume_raw_text or "", cgpa=payload.cgpa, graduation_year=payload.graduation_year, experience_months=payload.experience_months or 0, certifications=payload.certifications or [], jobs=jobs)

    for match in result["job_matches"]:
        await job_repo.upsert_match(str(student["_id"]), match["job_id"], {"match_score": match["match_score"], "score_breakdown": match["score_breakdown"], "missing_skills": match["missing_skills"], "placement_prediction": match["placement_prediction"]})

    return JobMatchResponse(
        job_matches=[JobMatchResult(job_id=m["job_id"], company=m["company"], role=m["role"], job_type=m.get("job_type","A"), match_score=m["match_score"], score_breakdown=ScoreBreakdown(**m["score_breakdown"]), missing_skills=m["missing_skills"], placement_prediction=m["placement_prediction"]) for m in result["job_matches"]],
        company_rankings=result["company_rankings"],
        match_probability=result["match_probability"],
        placement_prediction=result["placement_prediction"],
        total_jobs_analyzed=result["total_jobs_analyzed"],
    )


# ── Feature 4: Match Score Explainability ────────────────────────────────────
@router.post("/explain")
async def explain_score(payload: ExplainRequest, current_user=Depends(get_current_user)):
    """
    Human-readable breakdown of a job match score.
    Pass the score_breakdown from any job match result.
    """
    result = explain_match_score(
        payload.score_breakdown,
        payload.candidate_skills,
        payload.job_required_skills,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ── Feature 5: Company-wise Best Match Ranking ────────────────────────────────
@router.get("/company-rankings")
async def company_rankings(db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Get best matching job per company from student's saved job matches.
    Grouped and ranked by highest score.
    """
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch saved job matches for this student
    matches = await db.job_matches.find(
        {"student_id": str(student["_id"])}
    ).sort("match_score", -1).to_list(50)

    if not matches:
        raise HTTPException(status_code=404, detail="No job matches found. Run job matching first.")

    # Enrich with company + role from jobs collection
    enriched = []
    for m in matches:
        job = await db.jobs.find_one({"_id": m.get("job_id")}) if m.get("job_id") else None
        enriched.append({
            "company":              (job or {}).get("company", "Unknown Company"),
            "role":                 (job or {}).get("role", "Unknown Role"),
            "match_score":          m.get("match_score", 0),
            "placement_prediction": m.get("placement_prediction", "Unknown"),
        })

    result = rank_companies(enriched)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ── Feature 6: Skill Trend Analyzer ──────────────────────────────────────────
@router.get("/skill-trends")
async def skill_trends(db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Analyze top trending skills across all matched jobs.
    Returns top 10 in-demand skills + what you have vs missing.
    """
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get all active jobs with required_skills
    jobs_list = await db.jobs.find({"is_active": True}).to_list(100)
    job_dicts = [
        {"required_skills": j.get("required_skills", []), "missing_skills": []}
        for j in jobs_list
    ]

    # Get candidate's current skills from latest resume
    resume = await ResumeRepository(db).get_active_resume(str(student["_id"]))
    candidate_skills = [s.get("name", "") for s in (resume or {}).get("skills", [])]

    result = analyze_skill_trends(job_dicts, candidate_skills)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ── Feature 7: Adzuna Live Job Fetch ─────────────────────────────────────────
@router.get("/live")
async def fetch_live_jobs(
    role: str = Query(..., description="Job role to search, e.g. Python Developer"),
    location: str = Query(default="India", description="Location"),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Fetch live jobs from Adzuna API.
    Auto-fallback to static list if API unavailable.
    Embeds and saves fetched jobs to MongoDB.
    """
    result = get_jobs(role, location, db)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
