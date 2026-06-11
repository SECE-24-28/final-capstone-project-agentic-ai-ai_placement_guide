from datetime import datetime
from typing import Optional, List
from bson import ObjectId


def new_doc(**kwargs) -> dict:
    return {"_id": ObjectId(), "created_at": datetime.utcnow(), **kwargs}


def user_doc(email: str, hashed_password: str, role: str = "student") -> dict:
    return new_doc(email=email, hashed_password=hashed_password, role=role, is_active=True)


def student_doc(user_id: str, full_name: str) -> dict:
    return new_doc(
        user_id=user_id,
        full_name=full_name,
        phone=None,
        target_role=None,
        available_hours_per_day=2.0,
        cgpa=None,
        graduation_year=None,
        student_level="beginner",
        placement_status="not_ready",
    )


def resume_doc(student_id: str, file_path: str, file_name: str, analysis: dict) -> dict:
    return new_doc(
        student_id=student_id,
        file_path=file_path,
        file_name=file_name,
        raw_text=analysis.get("raw_text", ""),
        resume_score=analysis.get("resume_score", 0),
        embedding=analysis.get("embedding"),
        skills=analysis.get("skills", []),
        education=analysis.get("education", []),
        experience=analysis.get("experience", []),
        projects=analysis.get("projects", []),
        certifications=analysis.get("certifications", []),
        feedback=analysis.get("feedback", []),
        is_active=True,
    )
