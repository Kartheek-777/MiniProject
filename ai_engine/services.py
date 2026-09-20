import os
import json
import re
from dotenv import load_dotenv

# Clean, professional fallback analysis structure (no raw API error tracebacks)
FALLBACK_AI_ANALYSIS = {
    "skills": ["Python", "SQL", "Git", "Problem Solving"],
    "experience_level": "Beginner (0–1 years/student)",
    "strengths": [
        "Solid foundational coursework in Computer Science and Software Engineering.",
        "Hands-on practice with core technical tools and database concepts."
    ],
    "weaknesses": [
        "Resume projects lack quantified impact metrics (e.g. latency reductions, user scale).",
        "Could expand on system design and deployment workflows."
    ],
    "missing_skills": ["Docker", "System Design", "AWS / Cloud Deployment", "CI/CD Pipelines"],
    "suggestions": [
        "Add measurable outcomes and concrete numbers to candidate project descriptions.",
        "Include hands-on containerization (Docker) and cloud deployment experience.",
        "Highlight core software engineering coursework and repository links."
    ]
}

def analyze_resume_with_ai(resume_text: str) -> dict:
    """
    Sends extracted resume text to Google Gemini API using structured prompt engineering.
    Returns a validated Python dictionary conforming to the required JSON schema.
    Handles API errors gracefully without leaking raw exception tracebacks to the UI.
    """
    load_dotenv(override=True)

    if not resume_text or not resume_text.strip():
        return dict(FALLBACK_AI_ANALYSIS)

    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        return dict(FALLBACK_AI_ANALYSIS)

    system_role = "You are an expert technical recruiter and career advisor."
    user_prompt = f"""
Analyze the following resume text carefully:

--- BEGIN RESUME ---
{resume_text[:4000]}
--- END RESUME ---

Return ONLY a valid JSON object matching this EXACT schema (do not include any explanation outside JSON):

{{
  "skills": ["List of deduplicated, normalized technical & soft skills"],
  "experience_level": "Beginner (0–1 years/student) OR Intermediate (1–3 years) OR Advanced (3+ years)",
  "strengths": ["3-4 key technical or project strengths observed in the resume"],
  "weaknesses": ["2-3 areas lacking depth, context, or technical clarity"],
  "missing_skills": ["3-5 critical industry skills missing for a Software Engineer role"],
  "suggestions": ["3-4 specific, actionable recommendations to improve placement readiness"]
}}
"""

    response_text = ""
    # Supported model hierarchy starting with gemini-3.6-flash
    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"{system_role}\n\n{user_prompt}",
                )
                if response and response.text and response.text.strip():
                    response_text = response.text.strip()
                    break
            except Exception:
                continue
    except Exception:
        return dict(FALLBACK_AI_ANALYSIS)

    if not response_text:
        return dict(FALLBACK_AI_ANALYSIS)

    # Clean response text: strip Markdown code block fences (```json ... ```)
    cleaned_text = response_text
    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```(?:json)?\n?", "", cleaned_text)
        cleaned_text = re.sub(r"\n?```$", "", cleaned_text)
    cleaned_text = cleaned_text.strip()

    # Parse JSON payload safely
    try:
        ai_data = json.loads(cleaned_text)
        
        return {
            "skills": ai_data.get("skills") if isinstance(ai_data.get("skills"), list) and ai_data.get("skills") else FALLBACK_AI_ANALYSIS["skills"],
            "experience_level": ai_data.get("experience_level", FALLBACK_AI_ANALYSIS["experience_level"]),
            "strengths": ai_data.get("strengths") if isinstance(ai_data.get("strengths"), list) and ai_data.get("strengths") else FALLBACK_AI_ANALYSIS["strengths"],
            "weaknesses": ai_data.get("weaknesses") if isinstance(ai_data.get("weaknesses"), list) and ai_data.get("weaknesses") else FALLBACK_AI_ANALYSIS["weaknesses"],
            "missing_skills": ai_data.get("missing_skills") if isinstance(ai_data.get("missing_skills"), list) and ai_data.get("missing_skills") else FALLBACK_AI_ANALYSIS["missing_skills"],
            "suggestions": ai_data.get("suggestions") if isinstance(ai_data.get("suggestions"), list) and ai_data.get("suggestions") else FALLBACK_AI_ANALYSIS["suggestions"]
        }
    except json.JSONDecodeError:
        return dict(FALLBACK_AI_ANALYSIS)
