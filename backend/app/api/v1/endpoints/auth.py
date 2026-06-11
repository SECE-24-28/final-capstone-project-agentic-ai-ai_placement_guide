from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db=Depends(get_db)):
    repo = UserRepository(db)
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await repo.create(payload.email, payload.password, payload.full_name, payload.role)
    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token, user_id=str(user["_id"]), role=user["role"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db=Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token, user_id=str(user["_id"]), role=user["role"])
