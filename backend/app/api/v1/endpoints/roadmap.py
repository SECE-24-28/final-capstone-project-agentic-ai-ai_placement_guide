from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.core.security import get_current_user
from app.agents.roadmap.agent import generate_roadmap
from app.repositories.user_repo import StudentRepository
from app.repositories.job_repo import RoadmapRepository
from app.schemas.schemas import RoadmapRequest, RoadmapResponse

router = APIRouter(prefix="/roadmap", tags=["Roadmap Generator"])


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap_endpoint(payload: RoadmapRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    await StudentRepository(db).update(student, student_level=payload.student_level, available_hours_per_day=payload.available_hours_per_day, target_role=payload.target_role)
    result = await generate_roadmap(missing_skills=payload.missing_skills, student_level=payload.student_level, available_hours_per_day=payload.available_hours_per_day, target_role=payload.target_role)
    await RoadmapRepository(db).save(str(student["_id"]), result)
    return RoadmapResponse(**result)


@router.get("/latest", response_model=RoadmapResponse)
async def get_latest_roadmap(db=Depends(get_db), current_user=Depends(get_current_user)):
    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    roadmap = await RoadmapRepository(db).get_latest(str(student["_id"]))
    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap found. Run skill gap analysis first.")

    return RoadmapResponse(
        target_role=roadmap["target_role"],
        duration_weeks=roadmap["duration_weeks"],
        daily_plan=roadmap["daily_plan"],
        weekly_plan=roadmap["weekly_plan"],
        monthly_milestones=roadmap["monthly_milestones"],
        resources=roadmap["resources"],
        mock_interview_schedule=roadmap["mock_interview_schedule"],
    )
