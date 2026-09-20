import os
import json
import re
from dotenv import load_dotenv

def get_candidate_resume_context(user) -> str:
    """
    Fetches actual uploaded resume for user from resume_analyzer model if available.
    """
    try:
        from resume_analyzer.models import Resume
        resume = Resume.objects.filter(user=user).order_by('-uploaded_at').first()
        if resume:
            skills = ", ".join(resume.extracted_skills) if isinstance(resume.extracted_skills, list) and resume.extracted_skills else "Not explicitly parsed"
            education = json.dumps(resume.extracted_education) if resume.extracted_education else "Not parsed"
            projects = json.dumps(resume.extracted_projects) if resume.extracted_projects else "None extracted"
            text_snippet = (resume.extracted_text[:800] + "...") if resume.extracted_text else ""
            
            return f"""
👤 CANDIDATE RESUME CONTEXT (ATTACHED):
- Resume Title: {resume.title}
- Extracted Skills: {skills}
- Extracted Projects: {projects}
- Education: {education}
- Resume Text Excerpt: {text_snippet}
- NOTE FOR INTERVIEWER: Base project deep-dives & technical questions on these REAL projects/skills from the candidate's uploaded resume!
"""
    except Exception:
        pass

    return """
👤 CANDIDATE RESUME CONTEXT: NO RESUME UPLOADED
- NOTE FOR INTERVIEWER: The candidate has NOT uploaded a resume. Ask questions strictly based on general core engineering requirements for the target role. DO NOT invent or reference fake candidate projects (such as 'Resume Analyzer' or 'Job Matcher') unless the candidate explicitly mentions them in their answers.
"""


def build_system_interviewer_prompt(session) -> str:
    resume_context = get_candidate_resume_context(session.user)
    return f"""
You are an elite AI Technical Interview Engine for top-tier product engineering companies.

🎯 ROLE & PERSONA:
Act as a Senior Software Engineer + Technical Interviewer with 8+ years of industry experience.
Your job is NOT to be overly friendly or give away answers. Your job is to rigorously evaluate, challenge, probe, and test the candidate under professional pressure.

🎯 TARGET ROLE: {session.target_role}

{resume_context}

🧠 INTERVIEW PHASES (STRICT PROGRESSION):
1. HR Screening (Communication, background, intent, "Tell me about yourself")
2. Core CS Round (DSA, OOP, DBMS, OS fundamentals for {session.target_role})
3. Technical & Domain Round (Core concepts related to {session.target_role})
4. Project Deep Dive (Explore candidate's real resume projects or ask about past work experiences if no resume)
5. System Design (Beginner/Intermediate architecture scaling for {session.target_role})
6. Final Evaluation Ready

⚠️ INTERVIEW EXECUTION RULES:
- Ask ONLY ONE clear question at a time.
- DO NOT reveal full answers immediately.
- If candidate's answer is weak, incomplete, or vague: ask a probing follow-up or ask "WHY?".
- If candidate's answer is strong: increase difficulty or challenge their technical assumptions.
- Maintain a professional, sharp, and pressuring interviewer tone.
- When transitioning to a new phase, explicitly name the round (e.g. "[Phase 3: Core Technical]").
"""

EVALUATION_SYSTEM_PROMPT = """
You are an Executive Hiring Manager evaluating a candidate's complete technical interview transcript.

Return ONLY a valid JSON object matching this EXACT schema (do not include markdown text outside JSON):

{
  "rating": "7/10",
  "communication": "Strong / Average / Weak",
  "technical_skill": "Strong / Average / Weak",
  "project_understanding": "Strong / Average / Weak",
  "strengths": [
    "Specific candidate strength 1",
    "Specific candidate strength 2"
  ],
  "weaknesses": [
    "Specific candidate weakness 1",
    "Specific candidate weakness 2"
  ],
  "hire_decision": "Hire / No Hire",
  "improvements": [
    "Actionable improvement recommendation 1",
    "Actionable improvement recommendation 2",
    "Actionable improvement recommendation 3"
  ]
}
"""

def generate_interviewer_response(session, history_messages, latest_user_input: str) -> dict:
    """
    Generates the next turn from the AI Senior Technical Interviewer.
    Returns dict with keys: 'message', 'detected_phase', 'is_complete'
    """
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    system_prompt = build_system_interviewer_prompt(session)

    # Build conversation context for Gemini
    formatted_history = []
    for msg in history_messages:
        role_label = "Interviewer" if msg.sender == 'interviewer' else "Candidate"
        formatted_history.append(f"{role_label}: {msg.message}")

    if latest_user_input:
        formatted_history.append(f"Candidate: {latest_user_input}")

    history_text = "\n\n".join(formatted_history[-10:])  # last 10 turns for token efficiency

    user_prompt = f"""
Current Interview Mode: {session.interview_mode}
Current Phase: {session.current_phase}

--- RECENT CONVERSATION HISTORY ---
{history_text}
--- END HISTORY ---

Candidate's Latest Response: "{latest_user_input}"

Based on the candidate's latest response and the current interview phase ({session.current_phase}):
1. Evaluate if candidate answered adequately.
2. Formulate the next single interviewer response/question.
3. If candidate is ready to move to next round, indicate phase change.
4. Keep response under 150 words.

Return JSON in this format:
{{
  "response_text": "Your question or probing statement here",
  "phase": "HR Screening OR Core CS OR Technical Round OR Project Deep Dive OR System Design OR Final Evaluation",
  "is_interview_finished": false
}}
"""

    fallback_res = {
        "message": f"Thank you for your response. Let's move deeper into your technical background. Could you elaborate on key projects you have built or relevant core skills for {session.target_role}?",
        "detected_phase": session.current_phase,
        "is_complete": False
    }

    if not api_key:
        return {
            "message": f"Welcome to your AI Technical Mock Interview for the '{session.target_role}' position. Let's begin with Phase 1: HR Screening. Tell me about yourself, your background, and why you are targeting this role?",
            "detected_phase": "HR Screening",
            "is_complete": False
        }

    response_text = ""
    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        for model_name in models_to_try:
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=f"{system_prompt}\n\n{user_prompt}",
                )
                if res and res.text and res.text.strip():
                    response_text = res.text.strip()
                    break
            except Exception:
                continue
    except Exception:
        return fallback_res

    if not response_text:
        return fallback_res

    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        return {
            "message": data.get("response_text", "Could you elaborate further on that technical point?"),
            "detected_phase": data.get("phase", session.current_phase),
            "is_complete": data.get("is_interview_finished", False)
        }
    except Exception:
        return {
            "message": cleaned if cleaned else "Can you explain the trade-offs of your implementation?",
            "detected_phase": session.current_phase,
            "is_complete": False
        }


def evaluate_interview_session(session, history_messages) -> dict:
    """
    Evaluates transcript against standard rubric and produces final structured JSON report.
    """
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    candidate_msgs = [m for m in history_messages if m.sender == 'candidate' and m.message.strip()]

    # 1. Zero Candidate Responses
    if not candidate_msgs:
        return {
            "rating": "0.0/10",
            "communication": "Weak",
            "technical_skill": "Weak",
            "project_understanding": "Weak",
            "strengths": [
                "No candidate responses were recorded during the interview session."
            ],
            "weaknesses": [
                "Candidate ended the interview session without answering any questions.",
                "Technical competency could not be evaluated due to missing responses."
            ],
            "hire_decision": "No Hire",
            "improvements": [
                "Actively respond to interview questions using voice dictation or text input.",
                "Complete the core technical rounds before generating an evaluation scorecard."
            ]
        }

    total_candidate_words = sum(len(m.message.strip().split()) for m in candidate_msgs)

    # 2. Insufficient Answers (< 25 words total across candidate messages)
    if total_candidate_words < 25:
        return {
            "rating": "1.5/10",
            "communication": "Weak",
            "technical_skill": "Weak",
            "project_understanding": "Weak",
            "strengths": [
                "Candidate initiated the interview session."
            ],
            "weaknesses": [
                "Provided extremely brief responses with insufficient technical depth.",
                "Did not elaborate on technical concepts or project experience."
            ],
            "hire_decision": "No Hire",
            "improvements": [
                "Provide detailed, structured technical explanations to interview questions.",
                "Explain implementation trade-offs, architecture choices, and problem-solving steps."
            ]
        }

    formatted_history = []
    for msg in history_messages:
        role_label = "Interviewer" if msg.sender == 'interviewer' else "Candidate"
        formatted_history.append(f"[{msg.round_name}] {role_label}: {msg.message}")

    transcript = "\n".join(formatted_history)

    resume_context = get_candidate_resume_context(session.user)

    fallback_eval = {
        "rating": "5.0/10",
        "communication": "Average",
        "technical_skill": "Average",
        "project_understanding": "Average",
        "strengths": [
            "Attempted technical questions during the session.",
            "Demonstrated basic intent to pursue the role."
        ],
        "weaknesses": [
            "Needs deeper explanation of technical concepts and system design trade-offs.",
            "Answers lacked comprehensive detail and architectural structure."
        ],
        "hire_decision": "No Hire",
        "improvements": [
            "Study core engineering fundamentals and system design patterns.",
            "Practice articulating technical solutions clearly using structured frameworks.",
            "Build hands-on projects relevant to the target role."
        ]
    }

    if not api_key or not transcript.strip():
        return fallback_eval

    prompt = f"""
Candidate Target Role: {session.target_role}
Session Mode: {session.interview_mode}
{resume_context}

FULL INTERVIEW TRANSCRIPT:
---
{transcript}
---

Evaluate the candidate rigorously based ONLY on their actual transcript responses and resume background above. Do NOT invent fake projects.
Return the JSON payload conforming to the exact schema.
"""

    resp_text = ""
    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        for model_name in models_to_try:
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=f"{EVALUATION_SYSTEM_PROMPT}\n\n{prompt}"
                )
                if res and res.text and res.text.strip():
                    resp_text = res.text.strip()
                    break
            except Exception:
                continue
    except Exception:
        return fallback_eval

    if not resp_text:
        return fallback_eval

    cleaned = resp_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        eval_json = json.loads(cleaned)
        return {
            "rating": eval_json.get("rating", "5/10"),
            "communication": eval_json.get("communication", "Average"),
            "technical_skill": eval_json.get("technical_skill", "Average"),
            "project_understanding": eval_json.get("project_understanding", "Average"),
            "strengths": eval_json.get("strengths", ["Demonstrates core technical capabilities."]),
            "weaknesses": eval_json.get("weaknesses", ["Requires further preparation on advanced topics."]),
            "hire_decision": eval_json.get("hire_decision", "No Hire"),
            "improvements": eval_json.get("improvements", ["Continue technical practice and system design study."])
        }
    except Exception:
        return fallback_eval
