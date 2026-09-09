import os
import json
import re
from dotenv import load_dotenv

# Fallback response structure returned on API errors or missing keys
FALLBACK_AI_ANALYSIS = {
    "skills": [],
    "experience_level": "Unknown",
    "strengths": [],
    "weaknesses": ["AI service unavailable or API key unconfigured."],
    "missing_skills": [],
    "suggestions": ["Configure a valid GEMINI_API_KEY in your .env file to enable AI insights."]
}

def analyze_resume_with_ai(resume_text: str) -> dict:
    """
    Sends extracted resume text to Google Gemini API using structured prompt engineering.
    Returns a validated Python dictionary conforming to the required JSON schema.
    Handles errors gracefully without throwing exceptions.
    """
    # Reload .env fresh on each call
    load_dotenv(override=True)

    if not resume_text or not resume_text.strip():
        return {
            "skills": [],
            "experience_level": "Unknown",
            "strengths": [],
            "weaknesses": ["Empty or invalid resume text provided."],
            "missing_skills": [],
            "suggestions": ["Upload a resume containing readable text."]
        }

    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        return FALLBACK_AI_ANALYSIS

    # Construct System Persona & User Prompt
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

    # Primary SDK Execution: google.genai with gemini-3.6-flash
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{system_role}\n\n{user_prompt}",
        )
        response_text = response.text
    except Exception as e1:
        # Secondary Fallback: Try gemini-2.5-flash if gemini-3.6-flash fails
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_role}\n\n{user_prompt}",
            )
            response_text = response.text
        except Exception as e2:
            fallback = dict(FALLBACK_AI_ANALYSIS)
            fallback["weaknesses"] = [f"Gemini API Error: {str(e2)}"]
            return fallback

    if not response_text:
        return FALLBACK_AI_ANALYSIS

    # Clean response text: strip Markdown code block fences (```json ... ```)
    cleaned_text = response_text.strip()
    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```(?:json)?\n?", "", cleaned_text)
        cleaned_text = re.sub(r"\n?```$", "", cleaned_text)
    cleaned_text = cleaned_text.strip()

    # Parse JSON payload safely
    try:
        ai_data = json.loads(cleaned_text)
        
        # Enforce required JSON dictionary structure
        return {
            "skills": ai_data.get("skills", []),
            "experience_level": ai_data.get("experience_level", "Beginner (0–1 years/student)"),
            "strengths": ai_data.get("strengths", []),
            "weaknesses": ai_data.get("weaknesses", []),
            "missing_skills": ai_data.get("missing_skills", []),
            "suggestions": ai_data.get("suggestions", [])
        }
    except json.JSONDecodeError:
        fallback = dict(FALLBACK_AI_ANALYSIS)
        fallback["weaknesses"] = ["AI response returned invalid JSON formatting."]
        return fallback
