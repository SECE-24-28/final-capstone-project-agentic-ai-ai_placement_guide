from datetime import datetime
from bson import ObjectId
import numpy as np


def _cosine(a, b):
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


class JobRepository:
    def __init__(self, db):
        self.db = db

    async def get_all_active(self):
        return await self.db.jobs.find({"is_active": True}).to_list(None)

    async def semantic_search(self, query_embedding: list, top_k: int = 20):
        jobs = await self.get_all_active()
        scored = [(j, _cosine(query_embedding, j["embedding"])) for j in jobs if j.get("embedding")]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [j for j, _ in scored[:top_k]]

    async def upsert_match(self, student_id: str, job_id: str, match_data: dict):
        await self.db.job_matches.update_one(
            {"student_id": str(student_id), "job_id": str(job_id)},
            {"$set": {**match_data, "created_at": datetime.utcnow()}},
            upsert=True,
        )


class SkillGapRepository:
    def __init__(self, db):
        self.db = db

    async def save(self, student_id: str, data: dict) -> dict:
        doc = {"student_id": str(student_id), "created_at": datetime.utcnow(), **data}
        await self.db.skill_gaps.insert_one(doc)
        return doc

    async def get_latest(self, student_id: str):
        docs = await self.db.skill_gaps.find({"student_id": str(student_id)}).sort("created_at", -1).limit(1).to_list(1)
        return docs[0] if docs else None


class RoadmapRepository:
    def __init__(self, db):
        self.db = db

    async def save(self, student_id: str, data: dict) -> dict:
        doc = {"student_id": str(student_id), "created_at": datetime.utcnow(), **data}
        await self.db.roadmaps.insert_one(doc)
        return doc

    async def get_latest(self, student_id: str):
        docs = await self.db.roadmaps.find({"student_id": str(student_id)}).sort("created_at", -1).limit(1).to_list(1)
        return docs[0] if docs else None
