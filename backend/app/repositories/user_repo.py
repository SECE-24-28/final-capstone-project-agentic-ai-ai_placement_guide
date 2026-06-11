from bson import ObjectId
from app.core.security import hash_password
from app.models.models import user_doc, student_doc


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def create(self, email: str, password: str, full_name: str, role: str = "student") -> dict:
        user = user_doc(email=email, hashed_password=hash_password(password), role=role)
        await self.db.users.insert_one(user)
        if role == "student":
            s = student_doc(user_id=str(user["_id"]), full_name=full_name)
            await self.db.students.insert_one(s)
        return user

    async def get_by_email(self, email: str):
        return await self.db.users.find_one({"email": email})

    async def get_by_id(self, user_id: str):
        return await self.db.users.find_one({"_id": ObjectId(user_id)})


class StudentRepository:
    def __init__(self, db):
        self.db = db

    async def get_by_user_id(self, user_id: str):
        return await self.db.students.find_one({"user_id": str(user_id)})

    async def update(self, student: dict, **kwargs) -> dict:
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if updates:
            await self.db.students.update_one({"_id": student["_id"]}, {"$set": updates})
            student.update(updates)
        return student
