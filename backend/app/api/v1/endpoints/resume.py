import uuid
from datetime import datetime, timezone
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
    """Compare student's last 2 resume versions — section diff + ATS before/after."""
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resumes = await ResumeRepository(db).get_all_resumes(str(student["_id"]))

    if len(resumes) < 2:
        raise HTTPException(status_code=404, detail="Need at least 2 resume uploads to compare")

    # resumes[1] = older (v1), resumes[0] = newer (v2)
    result = compare_resume_versions(resumes[1], resumes[0])
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ── Resume History ────────────────────────────────────────────────────────────
@router.get("/history")
async def get_resume_history(db=Depends(get_db), current_user=Depends(get_current_user)):
    """Return all resume versions for this student, newest first."""
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resumes = await ResumeRepository(db).get_all_resumes(str(student["_id"]))
    if not resumes:
        raise HTTPException(status_code=404, detail="No resume history found")

    return {
        "total": len(resumes),
        "history": [
            {
                "resume_id":    str(r["_id"]),
                "file_name":    r.get("file_name", "resume"),
                "resume_score": r.get("resume_score", 0),
                "is_active":    r.get("is_active", False),
                "uploaded_at":  r.get("created_at").isoformat() if r.get("created_at") else None,
                "skills_count": len(r.get("skills", [])),
            }
            for r in resumes
        ],
    }


# ── Feature 2: Resume Strength Meter ─────────────────────────────────────────
@router.get("/strength")
async def get_resume_strength(db=Depends(get_db), current_user=Depends(get_current_user)):
    """Score latest resume across 5 criteria (20pts each). Returns breakdown + tips."""
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
    Tailor latest resume for a job description using spaCy + LLaMA 3.3 70B.
    Saves original + tailored versions to resume_versions collection (async).
    """
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resume = await ResumeRepository(db).get_active_resume(str(student["_id"]))
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Upload a resume first.")

    # Call sync function without db — we handle async saves below
    result = tailor_resume_for_job(resume, payload.job_description)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Async save both versions to MongoDB resume_versions collection
    now = datetime.now(timezone.utc)
    student_id = str(student["_id"])
    try:
        await db.resume_versions.insert_one({
            "student_id":   student_id,
            "version_type": "original",
            "resume":       {k: v for k, v in resume.items() if k != "_id"},
            "created_at":   now,
        })
        await db.resume_versions.insert_one({
            "student_id":   student_id,
            "version_type": "tailored",
            "resume":       {k: v for k, v in result["tailored_resume"].items() if k != "_id"},
            "jd_snippet":   payload.job_description[:300],
            "created_at":   now,
        })
    except Exception as e:
        # Non-fatal — still return tailored result
        result["db_save_warning"] = str(e)

    return result
