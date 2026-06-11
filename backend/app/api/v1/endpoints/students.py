from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.core.security import get_current_user
from app.repositories.user_repo import StudentRepository
from app.schemas.schemas import StudentProfileResponse, StudentProfileUpdate

router = APIRouter(prefix="/students", tags=["Student Profile"])


def _profile(student: dict, email: str) -> StudentProfileResponse:
    return StudentProfileResponse(
        id=str(student["_id"]),
        full_name=student.get("full_name"),
        email=email,
        phone=student.get("phone"),
        target_role=student.get("target_role"),
        cgpa=student.get("cgpa"),
        graduation_year=student.get("graduation_year"),
        student_level=student.get("student_level", "beginner"),
        placement_status=student.get("placement_status", "not_ready"),
        available_hours_per_day=student.get("available_hours_per_day", 2.0),
        created_at=student["created_at"],
    )


@router.get("/me", response_model=StudentProfileResponse)
async def get_profile(db=Depends(get_db), current_user=Depends(get_current_user)):
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return _profile(student, current_user["email"])


@router.patch("/me", response_model=StudentProfileResponse)
async def update_profile(payload: StudentProfileUpdate, db=Depends(get_db), current_user=Depends(get_current_user)):
    repo = StudentRepository(db)
    student = await repo.get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    updated = await repo.update(student, **payload.model_dump(exclude_none=True))
    return _profile(updated, current_user["email"])
