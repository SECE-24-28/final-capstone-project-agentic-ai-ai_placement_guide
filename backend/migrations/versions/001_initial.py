"""Initial schema with pgvector

Revision ID: 001_initial
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table("users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), default="student"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("students",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("phone", sa.String(20)),
        sa.Column("target_role", sa.String(255)),
        sa.Column("available_hours_per_day", sa.Float, default=2.0),
        sa.Column("cgpa", sa.Float),
        sa.Column("graduation_year", sa.Integer),
        sa.Column("student_level", sa.String(50), default="beginner"),
        sa.Column("placement_status", sa.String(50), default="not_ready"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("resumes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id")),
        sa.Column("file_path", sa.String(500)),
        sa.Column("file_name", sa.String(255)),
        sa.Column("raw_text", sa.Text),
        sa.Column("resume_score", sa.Float, default=0.0),
        sa.Column("embedding", Vector(384)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("skills",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id")),
        sa.Column("name", sa.String(100)),
        sa.Column("category", sa.String(100)),
        sa.Column("proficiency", sa.String(50)),
    )

    op.create_table("education",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id")),
        sa.Column("degree", sa.String(255)),
        sa.Column("institution", sa.String(255)),
        sa.Column("field_of_study", sa.String(255)),
        sa.Column("start_year", sa.Integer),
        sa.Column("end_year", sa.Integer),
        sa.Column("cgpa", sa.Float),
    )

    op.create_table("experience",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id")),
        sa.Column("company", sa.String(255)),
        sa.Column("role", sa.String(255)),
        sa.Column("start_date", sa.String(50)),
        sa.Column("end_date", sa.String(50)),
        sa.Column("description", sa.Text),
        sa.Column("duration_months", sa.Integer),
    )

    op.create_table("projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id")),
        sa.Column("name", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("tech_stack", sa.JSON),
        sa.Column("url", sa.String(500)),
    )

    op.create_table("certifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id")),
        sa.Column("name", sa.String(255)),
        sa.Column("issuer", sa.String(255)),
        sa.Column("year", sa.Integer),
    )

    op.create_table("resume_feedback",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id")),
        sa.Column("category", sa.String(100)),
        sa.Column("message", sa.Text),
        sa.Column("severity", sa.String(20), default="info"),
    )

    op.create_table("skill_gaps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id")),
        sa.Column("target_role", sa.String(255)),
        sa.Column("skill_gap_percentage", sa.Float),
        sa.Column("missing_skills", sa.JSON),
        sa.Column("priority_skills", sa.JSON),
        sa.Column("recommended_learning_order", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("roadmaps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id")),
        sa.Column("target_role", sa.String(255)),
        sa.Column("duration_weeks", sa.Integer),
        sa.Column("daily_plan", sa.JSON),
        sa.Column("weekly_plan", sa.JSON),
        sa.Column("monthly_milestones", sa.JSON),
        sa.Column("resources", sa.JSON),
        sa.Column("mock_interview_schedule", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("companies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), unique=True),
        sa.Column("industry", sa.String(255)),
        sa.Column("tier", sa.String(50)),
        sa.Column("website", sa.String(500)),
    )

    op.create_table("jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id")),
        sa.Column("role", sa.String(255)),
        sa.Column("required_skills", sa.JSON),
        sa.Column("min_cgpa", sa.Float),
        sa.Column("required_degree", sa.String(255)),
        sa.Column("batch_years", sa.JSON),
        sa.Column("min_experience_months", sa.Integer, default=0),
        sa.Column("required_certifications", sa.JSON),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("embedding", Vector(384)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("job_matches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id")),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("jobs.id")),
        sa.Column("match_score", sa.Float),
        sa.Column("score_breakdown", sa.JSON),
        sa.Column("missing_skills", sa.JSON),
        sa.Column("placement_prediction", sa.String(50)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "job_id"),
    )


def downgrade():
    for table in ["job_matches", "jobs", "companies", "roadmaps", "skill_gaps", "resume_feedback", "certifications", "projects", "experience", "education", "skills", "resumes", "students", "users"]:
        op.drop_table(table)
