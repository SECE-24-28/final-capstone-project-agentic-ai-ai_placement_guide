import re

def extract_skills(text):
    known_skills = [
        "python", "java", "c", "c++", "sql",
        "react", "node.js", "mongodb",
        "mysql", "postgresql",
        "html", "css", "javascript",
        "dsa", "oop", "dbms"
    ]

    text = text.lower()

    found = []

    for skill in known_skills:
        if skill in text:
            found.append(skill)

    return found


def calculate_score(resume_text, job_description):

    resume_skills = set(extract_skills(resume_text))

    job_skills = set(
        skill.strip().lower()
        for skill in job_description.split(",")
    )

    matched = resume_skills.intersection(job_skills)

    if len(job_skills) == 0:
        return 0, []

    score = (
        len(matched) /
        len(job_skills)
    ) * 100

    missing = list(job_skills - resume_skills)

    return round(score, 2), missing