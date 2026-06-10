import json
import fitz

from backend.app.agents.job_matching.scoring import calculate_score


def extract_text(pdf_path):
    text = ""

    pdf = fitz.open(pdf_path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


resume_text = extract_text("resume.pdf")
with open(
    "jobs_data.json",
    "r",
    encoding="utf-8"
) as f:
    jobs = json.load(f)

results = []

for job in jobs:

   score, missing = calculate_score(
    resume_text,
    job["description"]

    )

   results.append({
    "Company": job["company"],
    "Role": job["role"],
    "Score": score,
    "Missing": ", ".join(missing)
})

results.sort(
    key=lambda x: x["Score"],
    reverse=True
)

for idx, job in enumerate(results, start=1):

    print(
        f"\n{idx}. {job['Company']} | {job['Role']}"
    )

    print(
        f"Match Score: {job['Score']}%"
    )

    print(
        f"Missing Skills: {job['Missing']}"
    )