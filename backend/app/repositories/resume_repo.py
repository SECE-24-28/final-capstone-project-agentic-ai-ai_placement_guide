import hashlib
import uuid
from bson import ObjectId
from app.models.models import resume_doc


class ResumeRepository:
    def __init__(self, db):
        self.db = db

    async def save_analysis(self, student_id: str, file_path: str, file_name: str, analysis: dict) -> dict:
        # Content hash to prevent duplicate versions
        raw_text = analysis.get("raw_text", "")
        content_hash = hashlib.md5(raw_text.strip().encode()).hexdigest()

        # Check if same content already exists for this student
        existing = await self.db.resumes.find_one({"student_id": str(student_id), "content_hash": content_hash})
        if existing:
            # Same content — just make it active, don't create new version
            await self.db.resumes.update_many({"student_id": str(student_id), "is_active": True}, {"$set": {"is_active": False}})
            await self.db.resumes.update_one({"_id": existing["_id"]}, {"$set": {"is_active": True}})
            return existing

        # New content — deactivate previous and save new version
        await self.db.resumes.update_many({"student_id": str(student_id), "is_active": True}, {"$set": {"is_active": False}})
        doc = resume_doc(str(student_id), file_path, file_name, analysis)
        doc["content_hash"] = content_hash
        await self.db.resumes.insert_one(doc)
        return doc

    async def get_active_resume(self, student_id: str):
        return await self.db.resumes.find_one({"student_id": str(student_id), "is_active": True})

    async def get_all_resumes(self, student_id: str) -> list:
        """Return all resume versions for a student, newest first."""
        return await self.db.resumes.find(
            {"student_id": str(student_id)}
        ).sort("created_at", -1).to_list(None)
