from fastapi import APIRouter
from app.api.v1.endpoints import auth, resume, skill_gap, roadmap, jobs, pipeline, students

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(resume.router)
api_router.include_router(skill_gap.router)
api_router.include_router(roadmap.router)
api_router.include_router(jobs.router)
api_router.include_router(pipeline.router)
