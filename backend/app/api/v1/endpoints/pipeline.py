import uuid
import traceback
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from app.db.session import get_db
from app.core.security import get_current_user
from app.agents.resume_analyzer.agent import analyze_resume
from app.agents.skill_gap.agent import analyze_skill_gap
from app.agents.roadmap.agent import generate_roadmap
from app.agents.job_matching.agent import match_jobs
from app.repositories.resume_repo import ResumeRepository
from app.repositories.user_repo import StudentRepository
from app.repositories.job_repo import JobRepository, SkillGapRepository, RoadmapRepository
from app.schemas.schemas import (
    FullAnalysisResponse, ResumeAnalysisResponse, SkillGapResponse,
    RoadmapResponse, JobMatchResponse, JobMatchResult, ScoreBreakdown,
    SkillSchema, EducationSchema, ExperienceSchema, ProjectSchema, CertificationSchema, FeedbackSchema,
)
from app.core.config import settings
from app.core.embedder import embedder as _embedder

router = APIRouter(prefix="/analyze", tags=["Full Pipeline"])


@router.post("/full", response_model=FullAnalysisResponse)
async def full_analysis(
    resume: UploadFile = File(...),
    target_role: str = Form(...),
    student_level: str = Form(default="beginner"),
    available_hours_per_day: float = Form(default=2.0),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        file_bytes = await resume.read()
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = str(upload_dir / f"{uuid.uuid4()}_{resume.filename}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        student_repo = StudentRepository(db)
        student = await student_repo.get_by_user_id(str(current_user["_id"]))
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")

        # Agent 1
        analysis = await analyze_resume(file_bytes, resume.filename)
        await student_repo.update(student, full_name=analysis.get("candidate_name"), cgpa=analysis.get("cgpa"), graduation_year=analysis.get("graduation_year"), target_role=target_role, student_level=student_level, available_hours_per_day=available_hours_per_day)
        saved_resume = await ResumeRepository(db).save_analysis(str(student["_id"]), file_path, resume.filename, analysis)

        # Agent 2
        skill_names = [s["name"] for s in analysis.get("skills", [])]
        gap_result = await analyze_skill_gap(skill_names, target_role)
        await SkillGapRepository(db).save(str(student["_id"]), gap_result)

        # Agent 3
        roadmap_result = await generate_roadmap(missing_skills=gap_result["missing_skills"], student_level=student_level, available_hours_per_day=available_hours_per_day, target_role=target_role)
        await RoadmapRepository(db).save(str(student["_id"]), roadmap_result)

        # Agent 4
        job_repo = JobRepository(db)
        query_emb = _embedder.encode(target_role).tolist()
        jobs_list = await job_repo.semantic_search(query_emb, top_k=30)
        if len(jobs_list) < 5:
            jobs_list = await job_repo.get_all_active()

        jobs = [{"id": str(j["_id"]), "company": j["company"], "role": j["role"], "job_type": j.get("job_type", "A"), "required_skills": j.get("required_skills", []), "min_cgpa": j.get("min_cgpa"), "batch_years": j.get("batch_years"), "min_experience_months": j.get("min_experience_months", 0), "required_certifications": j.get("required_certifications")} for j in jobs_list]
        cert_names = [c["name"] for c in analysis.get("certifications", [])]
        match_result = await match_jobs(skills=skill_names, resume_score=analysis.get("resume_score", 0), cgpa=analysis.get("cgpa"), graduation_year=analysis.get("graduation_year"), experience_months=sum(ex.get("duration_months") or 0 for ex in analysis.get("experience", [])), certifications=cert_names, jobs=jobs)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        msg = str(e)
        if "invalid_api_key" in msg or "AuthenticationError" in type(e).__name__:
            raise HTTPException(status_code=500, detail="Invalid GROQ_API_KEY. Get a free key at https://console.groq.com and update backend/.env")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {msg}")

    return FullAnalysisResponse(
        resume_analysis=ResumeAnalysisResponse(
            resume_id=str(saved_resume["_id"]),
            candidate_name=analysis.get("candidate_name"),
            email=analysis.get("email"),
            phone=analysis.get("phone"),
            skills=[SkillSchema(**s) for s in analysis.get("skills", [])],
            education=[EducationSchema(**e) for e in analysis.get("education", [])],
            experience=[ExperienceSchema(**ex) for ex in analysis.get("experience", [])],
            projects=[ProjectSchema(**p) for p in analysis.get("projects", [])],
            certifications=[CertificationSchema(**c) for c in analysis.get("certifications", [])],
            cgpa=analysis.get("cgpa"),
            graduation_year=analysis.get("graduation_year"),
            resume_score=analysis.get("resume_score", 0),
            feedback=[FeedbackSchema(**f) for f in analysis.get("feedback", [])],
        ),
        skill_gap=SkillGapResponse(**gap_result),
        roadmap=RoadmapResponse(**roadmap_result),
        job_matches=JobMatchResponse(
            job_matches=[JobMatchResult(job_id=m["job_id"], company=m["company"], role=m["role"], job_type=m.get("job_type","A"), match_score=m["match_score"], score_breakdown=ScoreBreakdown(**m["score_breakdown"]), missing_skills=m["missing_skills"], placement_prediction=m["placement_prediction"]) for m in match_result["job_matches"]],
            company_rankings=match_result["company_rankings"],
            match_probability=match_result["match_probability"],
            placement_prediction=match_result["placement_prediction"],
            total_jobs_analyzed=match_result["total_jobs_analyzed"],
        ),
    )
