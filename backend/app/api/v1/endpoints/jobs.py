from fastapi import APIRouter, Depends, HTTPException
from sentence_transformers import SentenceTransformer

from app.db.session import get_db
from app.core.security import get_current_user
from app.agents.job_matching.agent import match_jobs
from app.repositories.user_repo import StudentRepository
from app.repositories.job_repo import JobRepository
from app.schemas.schemas import JobMatchRequest, JobMatchResponse, JobMatchResult, ScoreBreakdown

router = APIRouter(prefix="/jobs", tags=["Job Matching"])
_embedder = SentenceTransformer("all-MiniLM-L6-v2")


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

    jobs = [{"id": str(j["_id"]), "company": j["company"], "role": j["role"], "required_skills": j.get("required_skills", []), "min_cgpa": j.get("min_cgpa"), "batch_years": j.get("batch_years"), "min_experience_months": j.get("min_experience_months", 0), "required_certifications": j.get("required_certifications")} for j in jobs_list]

    result = await match_jobs(skills=payload.skills, resume_score=payload.resume_score, cgpa=payload.cgpa, graduation_year=payload.graduation_year, experience_months=payload.experience_months or 0, certifications=payload.certifications or [], jobs=jobs)

    for match in result["job_matches"]:
        await job_repo.upsert_match(str(student["_id"]), match["job_id"], {"match_score": match["match_score"], "score_breakdown": match["score_breakdown"], "missing_skills": match["missing_skills"], "placement_prediction": match["placement_prediction"]})

    return JobMatchResponse(
        job_matches=[JobMatchResult(job_id=m["job_id"], company=m["company"], role=m["role"], match_score=m["match_score"], score_breakdown=ScoreBreakdown(**m["score_breakdown"]), missing_skills=m["missing_skills"], placement_prediction=m["placement_prediction"]) for m in result["job_matches"]],
        company_rankings=result["company_rankings"],
        match_probability=result["match_probability"],
        placement_prediction=result["placement_prediction"],
        total_jobs_analyzed=result["total_jobs_analyzed"],
    )
