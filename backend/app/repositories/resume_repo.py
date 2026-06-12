from bson import ObjectId
from app.models.models import resume_doc


class ResumeRepository:
    def __init__(self, db):
        self.db = db

    async def save_analysis(self, student_id: str, file_path: str, file_name: str, analysis: dict) -> dict:
        # Deactivate previous resumes
        await self.db.resumes.update_many({"student_id": str(student_id), "is_active": True}, {"$set": {"is_active": False}})
        doc = resume_doc(str(student_id), file_path, file_name, analysis)
        await self.db.resumes.insert_one(doc)
        return doc

    async def get_active_resume(self, student_id: str):
        return await self.db.resumes.find_one({"student_id": str(student_id), "is_active": True})

    async def get_all_resumes(self, student_id: str) -> list:
        """Return all resume versions for a student, newest first."""
        return await self.db.resumes.find(
            {"student_id": str(student_id)}
        ).sort("created_at", -1).to_list(None)
