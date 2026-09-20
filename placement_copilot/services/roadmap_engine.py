import os
import json
import re
from dotenv import load_dotenv

from accounts.models import StudentProfile
from resume_analyzer.models import Resume
from job_matcher.models import JobMatch
from career.models import CareerRoadmap

def get_fallback_roadmap(target_role: str, current_skills: list, missing_skills: list, difficulty_level: str, duration_weeks: int = 6) -> dict:
    """
    Rule-based fallback weekly course roadmap generator used if AI API key is missing or service errors out.
    """
    sk1 = current_skills[:3] if current_skills else ["Python", "SQL", "Git"]
    m_sk = missing_skills if missing_skills else ["Docker", "System Design", "AWS Deployment", "CI/CD Pipelines"]
    topic = target_role or "Software Engineering"

    topic_templates = [
        (f"Foundations of {topic} & Environment Setup", sk1 + ["Environment Setup", "Core Syntax"], ["Official Documentation", "Interactive Practice"], "Complete environment setup and build initial code module."),
        (f"Core Data Structures & Algorithmic Problem Solving", ["Data Structures", "Algorithms"], ["LeetCode 75", "GeeksforGeeks"], "Solve 15 core technical exercises and document complexity patterns."),
        (f"Framework Architecture & Database Engineering", m_sk[:2] if len(m_sk)>=2 else ["Web Frameworks", "Database Tuning"], ["Framework Deep Dive Guide", "Database Operations"], "Implement a full database-driven web application module."),
        (f"Advanced Microservices & System Design", ["RESTful APIs", "System Design", "Redis Caching"], ["System Design Primer", "Postman API Guide"], "Build and secure high-throughput REST API endpoints with caching."),
        (f"Containerization, Testing & CI/CD Workflows", ["Docker Containerization", "Unit Testing", "GitHub Actions"], ["Docker Documentation", "GitHub Actions CI/CD Tutorial"], "Containerize application with Docker and configure automated CI/CD pipeline."),
        (f"Cloud Infrastructure & Capstone Deployment", ["Cloud Deployment", "AWS / GCP", "Portfolio Project"], ["Cloud Free Tier Labs", "Mock Technical Practice"], "Deploy project live to cloud environment and present capstone portfolio presentation.")
    ]

    weeks = []
    for w in range(1, duration_weeks + 1):
        tmpl_idx = (w - 1) % len(topic_templates)
        t_title, t_skills, t_res, t_milestone = topic_templates[tmpl_idx]
        weeks.append({
            "phase": f"Week {w}: {t_title}",
            "duration": f"Week {w}",
            "skills": t_skills,
            "resources": t_res,
            "milestone": f"Week {w} Milestone: {t_milestone}"
        })

    return {"roadmap": weeks}


def generate_career_roadmap(user, custom_target_role: str = None, duration_weeks: int = 6) -> CareerRoadmap:
    """
    Pipeline function:
    1. Collects UserProfile, Resume Skills, Job Match gaps, and ATS metrics.
    2. Determines difficulty level (Beginner <50%, Intermediate 50-75%, Advanced >75%).
    3. Prompts Gemini API for a structured N-Week Course Learning Roadmap.
    4. Saves to database as CareerRoadmap model instance.
    """
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    profile = StudentProfile.objects.filter(user=user).first()
    target_role = custom_target_role or (profile.target_role if profile and profile.target_role else 'Software Engineer')

    # Collect Extracted Resume Skills
    latest_resume = Resume.objects.filter(user=user).first()
    current_skills = []
    if latest_resume and isinstance(latest_resume.extracted_skills, list):
        current_skills = latest_resume.extracted_skills

    if not current_skills:
        current_skills = ["Python", "SQL", "Git", "Data Structures"]

    # Collect Missing Skills and Match Score from Job Matcher
    latest_match = JobMatch.objects.filter(user=user).first()
    match_score = latest_match.match_score if latest_match else 0
    missing_skills = []
    if latest_match and isinstance(latest_match.missing_skills, list):
        missing_skills = latest_match.missing_skills

    if not missing_skills:
        missing_skills = ["Docker", "System Design", "AWS Deployment", "CI/CD Pipelines"]

    # Smart Logic for Difficulty Level
    if match_score < 50:
        difficulty_level = 'Beginner'
    elif 50 <= match_score <= 75:
        difficulty_level = 'Intermediate'
    else:
        difficulty_level = 'Advanced'

    fallback_data = get_fallback_roadmap(target_role, current_skills, missing_skills, difficulty_level, duration_weeks)
    roadmap_json = fallback_data

    if api_key:
        system_prompt = "You are a Chief Technology Officer and Master Curriculum Architect designing weekly course learning roadmaps."
        user_prompt = f"""
Design a structured, week-by-week ({duration_weeks} Weeks) Course Learning Roadmap for the topic/course/target role: "{target_role}".

CANDIDATE CONTEXT:
- Candidate Name: {user.get_full_name() or user.username}
- Possessed Skills: {", ".join(current_skills)}
- Identified Skill Gaps: {", ".join(missing_skills)}
- Alignment Level: {match_score}% ({difficulty_level})

INSTRUCTIONS:
1. Break the course/topic into EXACTLY {duration_weeks} distinct weekly modules (Week 1, Week 2, ..., Week {duration_weeks}).
2. For each week, provide specific technical skills to master, recommended learning resources, and a concrete weekly hands-on project milestone.

OUTPUT STRICT JSON ONLY (no markdown outside JSON):
{{
  "roadmap": [
    {{
      "phase": "Week 1: [Module Title / Focus Topic]",
      "duration": "Week 1",
      "skills": ["Skill 1", "Skill 2"],
      "resources": ["Resource 1", "Resource 2"],
      "milestone": "Actionable weekly hands-on project milestone goal."
    }}
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
                        raw_text = res.text.strip()
                        if raw_text.startswith("```"):
                            raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                            raw_text = re.sub(r"\n?```$", "", raw_text)
                        raw_text = raw_text.strip()

                        parsed = json.loads(raw_text)
                        if isinstance(parsed, dict) and "roadmap" in parsed and len(parsed["roadmap"]) > 0:
                            roadmap_json = parsed
                            break
                except Exception:
                    continue
        except Exception:
            roadmap_json = fallback_data

    # Save to Database
    roadmap_obj = CareerRoadmap.objects.create(
        user=user,
        title=f"{duration_weeks}-Week Course Roadmap: {target_role} ({difficulty_level})",
        target_role=target_role,
        current_skills=current_skills,
        missing_skills=missing_skills,
        roadmap_json=roadmap_json,
        difficulty_level=difficulty_level
    )

    return roadmap_obj
