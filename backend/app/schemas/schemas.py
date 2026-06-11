from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    role: str = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


# ─── Resume ───────────────────────────────────────────────────────────────────

class SkillSchema(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None


class EducationSchema(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa: Optional[float] = None


class ExperienceSchema(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    duration_months: Optional[int] = None


class ProjectSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    url: Optional[str] = None


class CertificationSchema(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[int] = None


class FeedbackSchema(BaseModel):
    category: str
    message: str
    severity: str = "info"


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[SkillSchema] = []
    education: List[EducationSchema] = []
    experience: List[ExperienceSchema] = []
    projects: List[ProjectSchema] = []
    certifications: List[CertificationSchema] = []
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    resume_score: float = 0.0
    feedback: List[FeedbackSchema] = []


# ─── Skill Gap ────────────────────────────────────────────────────────────────

class SkillGapRequest(BaseModel):
    skills: List[str]
    target_role: str
    resume_id: Optional[int] = None


class SkillGapResponse(BaseModel):
    skill_gap_percentage: float
    matched_skills: List[str]
    missing_skills: List[str]
    priority_skills: List[str]
    recommended_learning_order: List[str]
    target_role: str


# ─── Roadmap ──────────────────────────────────────────────────────────────────

class RoadmapRequest(BaseModel):
    missing_skills: List[str]
    student_level: str = "beginner"
    available_hours_per_day: float = Field(default=2.0, ge=0.5, le=12.0)
    target_role: str


class ResourceSchema(BaseModel):
    skill: str
    title: str
    url: str
    type: str
    duration: Optional[str] = None


class RoadmapResponse(BaseModel):
    target_role: str
    duration_weeks: int
    daily_plan: List[dict]
    weekly_plan: List[dict]
    monthly_milestones: List[dict]
    resources: List[ResourceSchema]
    mock_interview_schedule: List[dict]


# ─── Job Matching ─────────────────────────────────────────────────────────────

class JobMatchRequest(BaseModel):
    skills: List[str]
    resume_score: float
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    experience_months: Optional[int] = 0
    certifications: Optional[List[str]] = []
    target_role: Optional[str] = None


class ScoreBreakdown(BaseModel):
    skill_score: float
    cgpa_score: Optional[float] = None
    experience_score: Optional[float] = None
    certification_score: Optional[float] = None
    resume_score: float
    criteria_used: List[str]


class JobMatchResult(BaseModel):
    job_id: str
    company: str
    role: str
    match_score: float
    score_breakdown: ScoreBreakdown
    missing_skills: List[str]
    placement_prediction: str


class JobMatchResponse(BaseModel):
    job_matches: List[JobMatchResult]
    company_rankings: List[dict]
    match_probability: float
    placement_prediction: str
    total_jobs_analyzed: int


# ─── Unified Pipeline ─────────────────────────────────────────────────────────

class FullAnalysisResponse(BaseModel):
    resume_analysis: ResumeAnalysisResponse
    skill_gap: SkillGapResponse
    roadmap: RoadmapResponse
    job_matches: JobMatchResponse


# ─── Student Profile ─────────────────────────────────────────────────────────

class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    target_role: Optional[str] = None
    available_hours_per_day: Optional[float] = None
    student_level: Optional[str] = None


class StudentProfileResponse(BaseModel):
    id: str
    full_name: Optional[str]
    email: str
    phone: Optional[str]
    target_role: Optional[str]
    cgpa: Optional[float]
    graduation_year: Optional[int]
    student_level: str
    placement_status: str
    available_hours_per_day: float
    created_at: datetime

    class Config:
        from_attributes = True
