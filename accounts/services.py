import os
from django.utils import timezone
from dotenv import load_dotenv

def generate_ai_profile_summary(user, profile, stats: dict, force_refresh: bool = False) -> str:
    """
    Generates or retrieves cached ATS-optimized professional summary using Gemini API.
    """
    # Return cached summary if available and refresh not requested
    if profile.ai_summary and not force_refresh:
        return profile.ai_summary

    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    name = user.get_full_name() or user.username
    degree = profile.degree or 'B.Tech'
    branch = profile.branch or 'Computer Science & Engineering'
    grad_year = profile.graduation_year or 2026
    target_role = profile.target_role or 'Software Engineer'
    college = profile.college or 'Engineering Institute'
    
    resumes_count = stats.get('resumes_count', 0)
    avg_match = stats.get('job_match_avg', 0)
    interview_score = stats.get('avg_interview_score', 'N/A')
    extracted_skills = stats.get('skills', [])

    skills_str = ", ".join(extracted_skills[:8]) if extracted_skills else "Python, SQL, Django, Web Development"

    fallback_summary = (
        f"{name} is an ambitious {degree} candidate in {branch} at {college} (Class of {grad_year}) targeting "
        f"roles as a {target_role}. Possessing technical proficiency in {skills_str}, {name} demonstrates high "
        f"placement readiness with {resumes_count} resumes evaluated and a {avg_match}% average job match alignment."
    )

    if not api_key:
        profile.ai_summary = fallback_summary
        profile.ai_summary_generated_at = timezone.now()
        profile.save()
        return fallback_summary

    system_prompt = "You are an executive ATS resume consultant and technical hiring manager."
    user_prompt = f"""
Generate an ATS-optimized, 3-5 line professional executive profile summary for an engineering candidate:
- Full Name: {name}
- Education: {degree} in {branch}, {college} (Class of {grad_year})
- Target Career Role: {target_role}
- Key Technical Skills: {skills_str}
- Platform Analytics: {resumes_count} Resumes Analyzed | {avg_match}% Job Match Score | {interview_score} Interview Rating

Write in third person ("{name} is..."). Highlight technical alignment, problem-solving mindset, and ATS keyword relevance.
Return ONLY the final 3-5 line paragraph text. No markdown fences or conversational preambles.
"""

    summary_text = fallback_summary

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        res = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{system_prompt}\n\n{user_prompt}"
        )
        if res.text and res.text.strip():
            summary_text = res.text.strip()
    except Exception:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_prompt}\n\n{user_prompt}"
            )
            if res.text and res.text.strip():
                summary_text = res.text.strip()
        except Exception:
            summary_text = fallback_summary

    # Cache in database
    profile.ai_summary = summary_text
    profile.ai_summary_generated_at = timezone.now()
    profile.save()

    return summary_text
