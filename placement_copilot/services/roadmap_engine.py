import os
import json
import re
from dotenv import load_dotenv

from accounts.models import StudentProfile
from resume_analyzer.models import Resume
from job_matcher.models import JobMatch
from career.models import CareerRoadmap

def get_fallback_roadmap(target_role: str, current_skills: list, missing_skills: list, difficulty_level: str) -> dict:
    """
    Rule-based fallback weekly course roadmap generator used if AI API key is missing or service errors out.
    """
    sk1 = current_skills[:3] if current_skills else ["Python", "SQL", "Git"]
    m_sk = missing_skills if missing_skills else ["Docker", "System Design", "AWS Deployment", "CI/CD Pipelines"]

    topic = target_role or "Software Engineering"

    return {
        "roadmap": [
            {
                "phase": f"Week 1: Foundations of {topic} & Core Syntax",
                "duration": "Week 1",
                "skills": sk1 + ["Environment Setup", "Core Language Mechanics"],
                "resources": [f"Official {topic} Documentation", "FreeCodeCamp Interactive Guide"],
                "milestone": f"Complete environment setup and build your first baseline prototype in {topic}."
            },
            {
                "phase": f"Week 2: Essential Algorithms & Skill Gap Bridging",
                "duration": "Week 2",
                "skills": m_sk[:2] if len(m_sk) >= 2 else ["Data Structures", "REST APIs"],
                "resources": ["LeetCode 75", "GeeksforGeeks Skill Gap Practice"],
                "milestone": "Solve 15 core technical exercises and document architecture patterns."
            },
            {
                "phase": f"Week 3: Framework Architecture & Database Systems",
                "duration": "Week 3",
                "skills": m_sk[2:4] if len(m_sk) >= 4 else ["Django / FastAPI", "PostgreSQL / SQL"],
                "resources": ["Framework Deep Dive Guide", "PostgreSQL Tuning Guide"],
                "milestone": "Implement a full database-driven web module with user authentication."
            },
            {
                "phase": f"Week 4: Advanced Services & System Design",
                "duration": "Week 4",
                "skills": ["RESTful APIs", "Redis Caching", "Async Processing"],
                "resources": ["System Design Primer", "Postman API Benchmark Guide"],
                "milestone": "Build and secure high-throughput REST API endpoints with caching."
            },
            {
                "phase": f"Week 5: Containerization, Testing & CI/CD",
                "duration": "Week 5",
                "skills": ["Docker Containerization", "Unit Testing", "GitHub Actions"],
                "resources": ["Docker Get Started", "GitHub Actions CI/CD Tutorial"],
                "milestone": "Containerize full application with Docker Compose and set up automated unit test workflow."
            },
            {
                "phase": f"Week 6: Cloud Deployment & Capstone Portfolio Project",
                "duration": "Week 6",
                "skills": ["AWS Cloud Deployment", "Monitoring", "Interview Preparation"],
                "resources": ["AWS Free Tier Labs", "Mock Technical Interview Practice"],
                "milestone": "Deploy project live to cloud environment and complete full capstone portfolio presentation."
            }
        ]
    }


def generate_career_roadmap(user, custom_target_role: str = None) -> CareerRoadmap:
    """
    Pipeline function:
    1. Collects UserProfile, Resume Skills, Job Match gaps, and ATS metrics.
    2. Determines difficulty level (Beginner <50%, Intermediate 50-75%, Advanced >75%).
    3. Prompts Gemini API for a structured 6-Week Course Learning Roadmap.
    4. Saves to database as CareerRoadmap model instance and triggers daily execution breakdown.
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

    fallback_data = get_fallback_roadmap(target_role, current_skills, missing_skills, difficulty_level)
    roadmap_json = fallback_data

    if api_key:
        system_prompt = "You are a Chief Technology Officer and Master Curriculum Architect designing weekly course learning roadmaps."
        user_prompt = f"""
Design a structured, week-by-week (6 Weeks) Course Learning Roadmap for the topic/course/target role: "{target_role}".

CANDIDATE CONTEXT:
- Candidate Name: {user.get_full_name() or user.username}
- Possessed Skills: {", ".join(current_skills)}
- Identified Skill Gaps: {", ".join(missing_skills)}
- Alignment Level: {match_score}% ({difficulty_level})

INSTRUCTIONS:
1. Break the course/topic into EXACTLY 6 distinct weekly modules (Week 1, Week 2, Week 3, Week 4, Week 5, Week 6).
2. For each week, provide specific technical skills to master, recommended learning resources, and a concrete weekly hands-on project milestone.

OUTPUT STRICT JSON ONLY (no markdown outside JSON):
{{
  "roadmap": [
    {{
      "phase": "Week 1: [Module Title / Focus Topic]",
      "duration": "Week 1",
      "skills": ["Skill 1", "Skill 2", "Skill 3"],
      "resources": ["Resource 1", "Resource 2"],
      "milestone": "Actionable weekly hands-on mini-project milestone goal."
    }},
    {{
      "phase": "Week 2: [Module Title / Focus Topic]",
      "duration": "Week 2",
      "skills": ["Skill 4", "Skill 5"],
      "resources": ["Resource 3", "Resource 4"],
      "milestone": "Actionable weekly hands-on milestone goal."
    }},
    {{
      "phase": "Week 3: [Module Title / Focus Topic]",
      "duration": "Week 3",
      "skills": ["Skill 6", "Skill 7"],
      "resources": ["Resource 5", "Resource 6"],
      "milestone": "Actionable weekly hands-on milestone goal."
    }},
    {{
      "phase": "Week 4: [Module Title / Focus Topic]",
      "duration": "Week 4",
      "skills": ["Skill 8", "Skill 9"],
      "resources": ["Resource 7", "Resource 8"],
      "milestone": "Actionable weekly hands-on milestone goal."
    }},
    {{
      "phase": "Week 5: [Module Title / Focus Topic]",
      "duration": "Week 5",
      "skills": ["Skill 10", "Skill 11"],
      "resources": ["Resource 9", "Resource 10"],
      "milestone": "Actionable weekly hands-on milestone goal."
    }},
    {{
      "phase": "Week 6: [Module Title / Capstone Project]",
      "duration": "Week 6",
      "skills": ["Skill 12", "Skill 13"],
      "resources": ["Resource 11", "Resource 12"],
      "milestone": "Final capstone project deployment & milestone goal."
    }}
  ]
}}
"""
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            res = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=f"{system_prompt}\n\n{user_prompt}"
            )
            raw_text = res.text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and "roadmap" in parsed and len(parsed["roadmap"]) > 0:
                roadmap_json = parsed
        except Exception:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"{system_prompt}\n\n{user_prompt}"
                )
                raw_text = res.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                    raw_text = re.sub(r"\n?```$", "", raw_text)
                raw_text = raw_text.strip()

                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "roadmap" in parsed and len(parsed["roadmap"]) > 0:
                    roadmap_json = parsed
            except Exception:
                roadmap_json = fallback_data

    # Save to Database
    roadmap_obj = CareerRoadmap.objects.create(
        user=user,
        title=f"6-Week Course Roadmap: {target_role} ({difficulty_level})",
        target_role=target_role,
        current_skills=current_skills,
        missing_skills=missing_skills,
        roadmap_json=roadmap_json,
        difficulty_level=difficulty_level
    )

    return roadmap_obj

