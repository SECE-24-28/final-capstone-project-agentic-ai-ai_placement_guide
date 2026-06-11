from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.core.security import get_current_user
from app.agents.skill_gap.agent import analyze_skill_gap
from app.repositories.user_repo import StudentRepository
from app.repositories.job_repo import SkillGapRepository
from app.schemas.schemas import SkillGapRequest, SkillGapResponse

router = APIRouter(prefix="/skill-gap", tags=["Skill Gap Analyzer"])


@router.post("/analyze", response_model=SkillGapResponse)
async def analyze_gap(payload: SkillGapRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    if not payload.skills:
        raise HTTPException(status_code=400, detail="Skills list cannot be empty")

    student = await StudentRepository(db).get_by_user_id(str(current_user["_id"]))
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    result = await analyze_skill_gap(payload.skills, payload.target_role)
    await StudentRepository(db).update(student, target_role=payload.target_role)
    await SkillGapRepository(db).save(str(student["_id"]), result)
    return SkillGapResponse(**result)
