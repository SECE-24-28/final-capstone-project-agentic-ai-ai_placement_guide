import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.agents.resume_analyzer.agent import analyze_resume
from app.repositories.resume_repo import ResumeRepository
from app.repositories.user_repo import StudentRepository
from app.schemas.schemas import (
    ResumeAnalysisResponse, SkillSchema, EducationSchema,
    ExperienceSchema, ProjectSchema, CertificationSchema, FeedbackSchema,
)
from app.services.features import (
    compare_resume_versions,
    resume_strength_meter,
    tailor_resume_for_job,
)


class TailorRequest(BaseModel):
    job_description: str

router = APIRouter(prefix="/resume", tags=["Resume Analyzer"])
ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume_endpoint(
    resume: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if resume.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are accepted")

    file_bytes = await resume.read()
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(upload_dir / f"{uuid.uuid4()}_{resume.filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    analysis = await analyze_resume(file_bytes, resume.filename)

    student_repo = StudentRepository(db)
    student = await student_repo.get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    await student_repo.update(student, full_name=analysis.get("candidate_name"), cgpa=analysis.get("cgpa"), graduation_year=analysis.get("graduation_year"))

    saved = await ResumeRepository(db).save_analysis(str(student["_id"]), file_path, resume.filename, analysis)

    return ResumeAnalysisResponse(
        resume_id=str(saved["_id"]),
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
        readiness_score=analysis.get("readiness_score", 0),
        feedback=[FeedbackSchema(**f) for f in analysis.get("feedback", [])],
    )


@router.get("/latest", response_model=ResumeAnalysisResponse)
async def get_latest_resume(db=Depends(get_db), current_user=Depends(get_current_user)):
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resume = await ResumeRepository(db).get_active_resume(str(student["_id"]))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload a resume first.")

    return ResumeAnalysisResponse(
        resume_id=str(resume["_id"]),
        resume_score=resume.get("resume_score", 0),
        skills=[SkillSchema(**s) for s in resume.get("skills", [])],
        education=[EducationSchema(**e) for e in resume.get("education", [])],
        experience=[ExperienceSchema(**ex) for ex in resume.get("experience", [])],
        projects=[ProjectSchema(**p) for p in resume.get("projects", [])],
        certifications=[CertificationSchema(**c) for c in resume.get("certifications", [])],
        feedback=[FeedbackSchema(**f) for f in resume.get("feedback", [])],
    )


# ── Feature 1: Resume Version Compare ────────────────────────────────────────
@router.get("/compare")
async def compare_resumes(db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Compare student's last 2 resume versions.
    Returns section-level diff + ATS score before vs after.
    """
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch last 2 resumes (most recent first)
    resumes = await db.resumes.find(
        {"student_id": str(student["_id"])}
    ).sort("created_at", -1).limit(2).to_list(2)

    if len(resumes) < 2:
        raise HTTPException(status_code=404, detail="Need at least 2 resume uploads to compare")

    # resumes[0] = newest, resumes[1] = older → compare older→newer
    result = compare_resume_versions(resumes[1], resumes[0])
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ── Feature 2: Resume Strength Meter ─────────────────────────────────────────
@router.get("/strength")
async def get_resume_strength(db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Score student's latest resume across 5 criteria (20pts each = 100 total).
    Returns overall score + per-section breakdown + improvement tips.
    """
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resume = await ResumeRepository(db).get_active_resume(str(student["_id"]))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Upload a resume first.")

    result = resume_strength_meter(resume)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ── Feature 3: Job-Specific Resume Tailoring ─────────────────────────────────
@router.post("/tailor")
async def tailor_resume(
    payload: TailorRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Tailor student's latest resume for a specific job description.
    Uses spaCy for keyword extraction + LLaMA 3.3 70B for rewriting.
    Saves both original and tailored versions to resume_versions collection.
    """
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resume = await ResumeRepository(db).get_active_resume(str(student["_id"]))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Upload a resume first.")

    result = tailor_resume_for_job(resume, payload.job_description, db)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
