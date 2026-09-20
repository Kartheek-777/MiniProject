import os
import json
import re
from dotenv import load_dotenv

from accounts.models import StudentProfile
from resume_analyzer.models import Resume
from job_matcher.models import JobListing, JobApplicationMatch, ApplicationAssist

INITIAL_JOBS_SEED = [
    {
        "title": "Software Development Engineer - I (Backend)",
        "company": "Amazon Web Services",
        "location": "Bengaluru, KA (Hybrid)",
        "description": "Building high-throughput microservices using Python, FastAPI, and AWS. Responsible for REST API design, database query optimization, and CI/CD pipelines.",
        "skills_required": ["Python", "SQL", "FastAPI", "RESTful APIs", "Docker", "AWS", "Data Structures"],
        "apply_link": "https://amazon.jobs/en/jobs/2541098"
    },
    {
        "title": "Generative AI & Machine Learning Engineer",
        "company": "OpenAI Partner Ecosystem",
        "location": "Remote / Hyderabad",
        "description": "Designing RAG pipelines, fine-tuning LLMs, vector search (FAISS/Pinecone), and prompt engineering frameworks for enterprise copilot applications.",
        "skills_required": ["Python", "Generative AI", "NLP", "PyTorch", "LangChain", "Vector DBs", "FastAPI"],
        "apply_link": "https://openai.com/careers"
    },
    {
        "title": "Full Stack Web Engineer (Django + React)",
        "company": "Swiggy Engineering",
        "location": "Bengaluru, KA",
        "description": "Developing customer-facing web platforms, real-time tracking dashboards, and scalable backend infrastructure with Python, Django, PostgreSQL, and React.js.",
        "skills_required": ["Python", "Django", "React.js", "SQL", "PostgreSQL", "Git", "REST APIs"],
        "apply_link": "https://swiggy.careers/jobs"
    },
    {
        "title": "Data & Analytics Platform Engineer",
        "company": "Razorpay Payments",
        "location": "Bengaluru / Remote",
        "description": "Scaling data transformation pipelines, warehousing (Snowflake/BigQuery), and real-time financial metrics aggregation using SQL, Python, and Airflow.",
        "skills_required": ["Python", "SQL", "Database Optimization", "Data Modeling", "Git", "AWS"],
        "apply_link": "https://razorpay.com/jobs"
    },
    {
        "title": "Cloud Infrastructure & DevOps Engineer",
        "company": "Google Cloud Partner",
        "location": "Hyderabad, TS",
        "description": "Automating cloud infrastructure provisioning with Terraform, managing Kubernetes clusters, and establishing automated CI/CD deployment pipelines.",
        "skills_required": ["Docker", "Kubernetes", "AWS", "CI/CD Pipelines", "Linux", "Python", "Git"],
        "apply_link": "https://careers.google.com"
    },
    {
        "title": "Product Engineer (Python & System Design)",
        "company": "Stripe Engineering",
        "location": "Remote (India)",
        "description": "Architecting resilient financial web products, designing public developer APIs, and ensuring 99.99% uptime for global transaction systems.",
        "skills_required": ["Python", "System Design", "SQL", "Django", "Docker", "RESTful APIs"],
        "apply_link": "https://stripe.com/jobs"
    }
]

def populate_initial_jobs():
    """
    Seeds database with initial high-quality product engineering job listings if none exist.
    """
    if JobListing.objects.count() == 0:
        for job_data in INITIAL_JOBS_SEED:
            JobListing.objects.create(**job_data)


def evaluate_candidate_job_matches(user) -> list:
    """
    Evaluates candidate's skills against all JobListing records, ranks by match score %,
    and marks the top recommendation.
    """
    populate_initial_jobs()

    latest_resume = Resume.objects.filter(user=user).first()
    candidate_skills = []
    if latest_resume and isinstance(latest_resume.extracted_skills, list):
        candidate_skills = [s.strip().lower() for s in latest_resume.extracted_skills if s.strip()]

    if not candidate_skills:
        candidate_skills = ["python", "sql", "git", "data structures", "django"]

    jobs = JobListing.objects.filter(is_active=True)
    matches_list = []

    for job in jobs:
        req_skills = job.skills_required or []
        req_skills_lower = [s.strip().lower() for s in req_skills]

        matched = []
        missing = []

        for orig_skill, s_lower in zip(req_skills, req_skills_lower):
            if any(cand_s in s_lower or s_lower in cand_s for cand_s in candidate_skills):
                matched.append(orig_skill)
            else:
                missing.append(orig_skill)

        score = (len(matched) / max(1, len(req_skills))) * 100.0
        score = round(score, 1)

        match_obj, _ = JobApplicationMatch.objects.update_or_create(
            user=user,
            job=job,
            defaults={
                "match_score": score,
                "matched_skills": matched,
                "missing_skills": missing
            }
        )
        matches_list.append(match_obj)

    # Sort descending by match_score
    matches_list.sort(key=lambda m: m.match_score, reverse=True)
    return matches_list


def generate_apply_assist(user, job: JobListing) -> ApplicationAssist:
    """
    Generates tailored Cover Letter and Resume Tips for a specific JobListing using Gemini API.
    """
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    # Check if assistance already exists
    existing = ApplicationAssist.objects.filter(user=user, job=job).first()
    if existing:
        return existing

    profile = StudentProfile.objects.filter(user=user).first()
    name = user.get_full_name() or user.username
    target_role = profile.target_role if profile and profile.target_role else "Software Engineer"
    college = profile.college if profile else "Engineering Institute"
    degree = profile.degree if profile else "B.Tech"
    branch = profile.branch if profile else "Computer Science"

    latest_resume = Resume.objects.filter(user=user).first()
    skills = latest_resume.extracted_skills if (latest_resume and latest_resume.extracted_skills) else ["Python", "SQL", "Django"]

    match_obj = JobApplicationMatch.objects.filter(user=user, job=job).first()
    missing_skills = match_obj.missing_skills if (match_obj and match_obj.missing_skills) else []

    fallback_cover_letter = (
        f"Dear Hiring Manager at {job.company},\n\n"
        f"I am writing to express my enthusiastic interest in the {job.title} position. As a {degree} student in {branch} at {college} with a strong foundation in {', '.join(skills[:4])}, I have developed a passion for building reliable software solutions.\n\n"
        f"My background in full-stack web development and database modeling aligns directly with the core requirements of your engineering team. I am eager to leverage my technical skills to contribute immediately to {job.company}'s product roadmap.\n\n"
        f"Thank you for considering my application. I look forward to discussing how my experience can support your team's goals.\n\n"
        f"Sincerely,\n{name}"
    )

    fallback_suggestions = [
        f"Highlight your experience with {skills[0] if skills else 'Python'} at the top of your resume skills section.",
        f"Address missing key requirements like '{missing_skills[0]}' by citing relevant project coursework or learning modules." if missing_skills else "Quantify project metrics with concrete numbers (e.g. API latency reductions or user counts).",
        f"Tailor your resume project titles to emphasize core competencies required for {job.title}."
    ]

    cover_letter = fallback_cover_letter
    suggestions = fallback_suggestions

    if api_key:
        system_prompt = "You are an elite Career Advisor writing ATS-optimized candidate cover letters and application materials."
        user_prompt = f"""
Write a professional, highly persuasive Cover Letter and Resume Optimization Suggestions for candidate applying to job:

CANDIDATE PROFILE:
- Name: {name}
- Target Role: {target_role}
- Education: {degree} in {branch}, {college}
- Possessed Skills: {", ".join(skills)}

JOB LISTING:
- Position Title: {job.title}
- Company Name: {job.company}
- Location: {job.location}
- Job Description: {job.description}
- Identified Skill Gaps: {", ".join(missing_skills) if missing_skills else "None"}

OUTPUT STRICT JSON ONLY:
{{
  "cover_letter": "Full personalized cover letter text (3-4 paragraphs)...",
  "suggestions": [
    "Specific resume tip 1",
    "Specific resume tip 2",
    "Specific resume tip 3"
  ]
}}
"""

        models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']
        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            for model_name in models_to_try:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=f"{system_prompt}\n\n{user_prompt}"
                    )
                    if res and res.text and res.text.strip():
                        raw = res.text.strip()
                        if raw.startswith("```"):
                            raw = re.sub(r"^```(?:json)?\n?", "", raw)
                            raw = re.sub(r"\n?```$", "", raw)
                        raw = raw.strip()

                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            cover_letter = parsed.get("cover_letter", fallback_cover_letter)
                            suggestions = parsed.get("suggestions", fallback_suggestions)
                            break
                except Exception:
                    continue
        except Exception:
            cover_letter = fallback_cover_letter
            suggestions = fallback_suggestions

    assist = ApplicationAssist.objects.create(
        user=user,
        job=job,
        cover_letter=cover_letter,
        suggestions=suggestions
    )
    return assist
