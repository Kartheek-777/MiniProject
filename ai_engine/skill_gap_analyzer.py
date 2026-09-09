import os
import json
import re
from collections import Counter
from dotenv import load_dotenv
from job_matcher.models import SkillGapHistory

def analyze_skill_gap_progress(user) -> dict:
    """
    Analyzes user's skill gap history over time and returns analytics payload + Gemini AI insights.
    """
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    # Fetch last 10 history entries ascending by time
    history = list(SkillGapHistory.objects.filter(user=user).order_by('created_at')[:10])

    if len(history) < 2:
        return {
            "has_enough_data": False,
            "message": "Not enough data yet. Run 2 or more Job Matches to unlock real-time progress analytics!",
            "scores": [float(h.match_score) for h in history],
            "dates": [h.created_at.strftime("%b %d %H:%M") for h in history],
            "top_missing_skills": [],
            "acquired_skills": [],
            "improvement_percentage": "0%",
            "ai_insights": {
                "improvement": "Stable",
                "strong_skills": [],
                "weak_skills": [],
                "recommendations": ["Run additional job description matches to begin tracking skill progress trends."]
            }
        }

    # Time series data
    dates = [h.created_at.strftime("%b %d %H:%M") for h in history]
    scores = [float(h.match_score) for h in history]

    # Frequency analysis for missing skills
    missing_counter = Counter()
    matched_counter = Counter()

    for h in history:
        if isinstance(h.skills_missing, list):
            for s in h.skills_missing:
                missing_counter[s] += 1
        if isinstance(h.skills_matched, list):
            for s in h.skills_matched:
                matched_counter[s] += 1

    top_missing_skills = [{"skill": k, "count": v} for k, v in missing_counter.most_common(8)]
    top_matched_skills = [k for k, _ in matched_counter.most_common(6)]

    # Calculate acquired skills (missing in earlier runs but present in recent matched skills)
    earliest_missing = set(history[0].skills_missing) if isinstance(history[0].skills_missing, list) else set()
    latest_matched = set(history[-1].skills_matched) if isinstance(history[-1].skills_matched, list) else set()
    acquired_skills = list(earliest_missing.intersection(latest_matched))

    # Calculate Improvement Percentage
    earliest_score = scores[0]
    latest_score = scores[-1]
    diff = latest_score - earliest_score
    if diff > 0:
        improvement_percentage = f"+{round(diff, 1)}%"
        status_label = "Improved"
    elif diff < 0:
        improvement_percentage = f"{round(diff, 1)}%"
        status_label = "Declined"
    else:
        improvement_percentage = "0%"
        status_label = "Stable"

    # Default Fallback AI insights
    fallback_insights = {
        "improvement": status_label,
        "strong_skills": top_matched_skills[:4] if top_matched_skills else ["Python", "SQL", "Git"],
        "weak_skills": [item["skill"] for item in top_missing_skills[:4]] if top_missing_skills else ["Docker", "AWS"],
        "recommendations": [
            f"Focus on mastering '{top_missing_skills[0]['skill']}' to significantly increase match alignment." if top_missing_skills else "Continue practicing target job skill requirements.",
            "Complete interactive project modules to convert missing skills into verified capabilities."
        ]
    }

    ai_insights = fallback_insights

    if api_key:
        system_prompt = "You are a Senior Talent Analytics Lead and Engineering Career Coach."
        user_prompt = f"""
Analyze the candidate's skill gap history trends across multiple job matches:

CANDIDATE ANALYTICS:
- Earliest Match Score: {earliest_score}% -> Latest Match Score: {latest_score}%
- Overall Trend: {improvement_percentage} ({status_label})
- Most Frequently Missing Skills: {", ".join([item['skill'] for item in top_missing_skills])}
- Acquired / Verified Skills: {", ".join(acquired_skills) if acquired_skills else "None yet"}

OUTPUT FORMAT (STRICT JSON ONLY, no markdown explanations outside JSON):
{{
  "improvement": "Improved / Declined / Stable",
  "strong_skills": ["Skill 1", "Skill 2"],
  "weak_skills": ["Weak Skill 1", "Weak Skill 2"],
  "recommendations": [
    "Actionable, high-impact recommendation 1",
    "Actionable, high-impact recommendation 2"
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
            raw = res.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "improvement" in parsed:
                ai_insights = parsed
        except Exception:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"{system_prompt}\n\n{user_prompt}"
                )
                raw = res.text.strip()
                if raw.startswith("```"):
                    raw = re.sub(r"^```(?:json)?\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                raw = raw.strip()
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "improvement" in parsed:
                    ai_insights = parsed
            except Exception:
                ai_insights = fallback_insights

    return {
        "has_enough_data": True,
        "scores": scores,
        "dates": dates,
        "top_missing_skills": top_missing_skills,
        "acquired_skills": acquired_skills,
        "improvement_percentage": improvement_percentage,
        "ai_insights": ai_insights
    }
