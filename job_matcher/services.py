import os
import json
import re
from dotenv import load_dotenv
from resume_analyzer.services import SKILLS_VOCABULARY

FALLBACK_JOB_MATCH_AI = {
    "fit_level": "Moderate Fit",
    "match_summary": "Rule-based skill matching completed. AI qualitative analysis unavailable.",
    "additional_missing_skills": [],
    "recommendations": [
        "Focus on bridging the missing rule-based technical skills highlighted below.",
        "Ensure your resume explicitly details project accomplishments using target keywords."
    ]
}

def extract_skills_from_jd(text: str) -> list:
    """
    Extracts technical skills from Job Description text using keyword matching.
    """
    if not text:
        return []
    
    found_skills = set()
    text_lower = text.lower()
    for skill in SKILLS_VOCABULARY:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)

    return sorted(list(found_skills))


def compute_rule_match(resume_skills: list, jd_skills: list) -> dict:
    """
    Calculates deterministic set intersection & match percentage:
    Match Score = (Matched Skills / JD Skills) * 100
    """
    if not jd_skills:
        return {
            'match_score': 0,
            'matched_skills': [],
            'missing_skills': []
        }

    # Case-insensitive comparison mapping
    resume_skills_lower = {s.lower(): s for s in resume_skills}
    
    matched = []
    missing = []

    for s in jd_skills:
        if s.lower() in resume_skills_lower:
            matched.append(s)
        else:
            missing.append(s)

    score = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0

    return {
        'match_score': score,
        'matched_skills': matched,
        'missing_skills': missing
    }


def analyze_job_match_with_ai(resume_text: str, job_title: str, job_description: str) -> dict:
    """
    Calls Google Gemini API (gemini-3.6-flash) to perform contextual fit analysis
    between the candidate's resume text and the target Job Description.
    """
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    if not api_key or not resume_text or not job_description:
        return FALLBACK_JOB_MATCH_AI

    system_role = "You are an expert technical recruiter evaluating candidate job fit."
    user_prompt = f"""
Evaluate the candidate's resume against the target Job Description.

Target Job Title: {job_title}

--- BEGIN JOB DESCRIPTION ---
{job_description[:3000]}
--- END JOB DESCRIPTION ---

--- BEGIN CANDIDATE RESUME ---
{resume_text[:3000]}
--- END CANDIDATE RESUME ---

Return ONLY a valid JSON object matching this EXACT schema (no text outside JSON):

{{
  "fit_level": "Strong Fit OR Moderate Fit OR Low Fit",
  "match_summary": "2-3 clear sentences summarizing candidate fit, strengths, and alignment for this role.",
  "additional_missing_skills": ["2-4 conceptual or technical skill gaps specific to this job"],
  "recommendations": ["3-4 actionable steps for the student to tailor their resume or prepare for this role"]
}}
"""

    response_text = ""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{system_role}\n\n{user_prompt}",
        )
        response_text = response.text
    except Exception as e:
        fallback = dict(FALLBACK_JOB_MATCH_AI)
        fallback["match_summary"] = f"Rule-based match calculated. AI Service Note: {str(e)}"
        return fallback

    if not response_text:
        return FALLBACK_JOB_MATCH_AI

    # Clean response text: strip Markdown code block fences
    cleaned_text = response_text.strip()
    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```(?:json)?\n?", "", cleaned_text)
        cleaned_text = re.sub(r"\n?```$", "", cleaned_text)
    cleaned_text = cleaned_text.strip()

    try:
        ai_data = json.loads(cleaned_text)
        return {
            "fit_level": ai_data.get("fit_level", "Moderate Fit"),
            "match_summary": ai_data.get("match_summary", "Candidate matches key software engineering requirements."),
            "additional_missing_skills": ai_data.get("additional_missing_skills", []),
            "recommendations": ai_data.get("recommendations", [])
        }
    except json.JSONDecodeError:
        return FALLBACK_JOB_MATCH_AI
