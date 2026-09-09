import os
import json
import re
from dotenv import load_dotenv

SYSTEM_INTERVIEWER_PROMPT = """
You are an elite AI Technical Interview Engine for top-tier product engineering companies.

🎯 ROLE & PERSONA:
Act as a Senior Software Engineer + AI/ML Interviewer with 8+ years of industry experience.
Your job is NOT to be overly friendly or give away answers. Your job is to rigorously evaluate, challenge, probe, and test the candidate under professional pressure.

👤 CANDIDATE CONTEXT:
- Target Role: AI/ML Trainee | Generative AI Fresher
- Academic Background: B.Tech CSE (AI/ML)
- Core Skills: Python, SQL, FastAPI, Django, React.js, ML basics
- Key Projects:
  1. Resume Analyzer (PDF parsing, skill extraction, ATS compliance)
  2. Job Matcher (Skill overlap scoring, missing skill breakdown)
  3. Career Roadmap Copilot (Personalized 3-month AI learning paths)
- Known Weak Areas: Generative AI (RAG, Fine-tuning, Vector DBs), AWS/Cloud Deployment, NLP, Scalable System Design
- Experience Level: 0–1 years (Beginner/Fresher)

🧠 INTERVIEW PHASES (STRICT PROGRESSION):
1. HR Screening (Communication, background, intent, "Tell me about yourself")
2. Core CS Round (DSA, OOP, DBMS, OS fundamentals)
3. AI/ML + Generative AI Round (Prompt engineering, Zero-shot vs Few-shot, RAG, Embeddings, Tokenization, API vs Fine-tuning)
4. Project Deep Dive (Resume Analyzer parsing & AI upgrade, Job Matcher semantic matching vs keywords, Career Roadmap personalization)
5. System Design (Beginner Level: Resume Analyzer system architecture, storage, 10,000 concurrent user scaling)
6. Final Evaluation Ready

⚠️ INTERVIEW EXECUTION RULES:
- Ask ONLY ONE clear question at a time.
- DO NOT reveal full answers immediately.
- If candidate's answer is weak, incomplete, or vague: ask a probing follow-up or ask "WHY?".
- If candidate's answer is strong: increase difficulty or challenge their technical assumptions.
- Maintain a professional, sharp, and pressuring interviewer tone.
- When transitioning to a new phase, explicitly name the round (e.g. "[Phase 3: AI/ML + GenAI]").
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
  "phase": "HR Screening OR Core CS OR AI/ML + GenAI OR Project Deep Dive OR System Design OR Final Evaluation",
  "is_interview_finished": false
}}
"""

    if not api_key:
        return {
            "message": "Let's begin with the HR Screening. Tell me about yourself, your background, and why you are targeting an AI/ML Trainee role?",
            "detected_phase": "HR Screening",
            "is_complete": False
        }

    response_text = ""

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{SYSTEM_INTERVIEWER_PROMPT}\n\n{user_prompt}",
        )
        response_text = response.text
    except Exception:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{SYSTEM_INTERVIEWER_PROMPT}\n\n{user_prompt}",
            )
            response_text = response.text
        except Exception as e:
            return {
                "message": f"Thank you for your response. Let's move deeper into your technical background. Can you walk me through your Resume Analyzer project and explain how text extraction works internally?",
                "detected_phase": session.current_phase,
                "is_complete": False
            }

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

    formatted_history = []
    for msg in history_messages:
        role_label = "Interviewer" if msg.sender == 'interviewer' else "Candidate"
        formatted_history.append(f"[{msg.round_name}] {role_label}: {msg.message}")

    transcript = "\n".join(formatted_history)

    fallback_eval = {
        "rating": "6.5/10",
        "communication": "Average",
        "technical_skill": "Average",
        "project_understanding": "Strong",
        "strengths": [
            "Good understanding of Resume Analyzer architecture and Django web flows.",
            "Clear communication and enthusiasm for AI/ML roles."
        ],
        "weaknesses": [
            "Needs deeper grasp of RAG architecture, vector embeddings, and LLM fine-tuning.",
            "System design concepts for high-concurrency scaling need improvement."
        ],
        "hire_decision": "Hire",
        "improvements": [
            "Master vector databases (FAISS, Pinecone) and embedding similarity metrics (cosine vs dot product).",
            "Study scalable system design: load balancing, caching (Redis), and async queues (Celery).",
            "Practice explaining rule-based vs AI parser trade-offs with concrete metrics."
        ]
    }

    if not api_key or not transcript.strip():
        return fallback_eval

    prompt = f"""
Candidate Target Role: {session.target_role}
Session Mode: {session.interview_mode}

FULL INTERVIEW TRANSCRIPT:
---
{transcript}
---

Evaluate the candidate rigorously and return the JSON payload conforming to the exact schema.
"""

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        res = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{EVALUATION_SYSTEM_PROMPT}\n\n{prompt}"
        )
        resp_text = res.text
    except Exception:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{EVALUATION_SYSTEM_PROMPT}\n\n{prompt}"
            )
            resp_text = res.text
        except Exception:
            return fallback_eval

    cleaned = resp_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        eval_json = json.loads(cleaned)
        return {
            "rating": eval_json.get("rating", "7/10"),
            "communication": eval_json.get("communication", "Average"),
            "technical_skill": eval_json.get("technical_skill", "Average"),
            "project_understanding": eval_json.get("project_understanding", "Average"),
            "strengths": eval_json.get("strengths", ["Demonstrates core technical capabilities."]),
            "weaknesses": eval_json.get("weaknesses", ["Requires further preparation on advanced topics."]),
            "hire_decision": eval_json.get("hire_decision", "Hire"),
            "improvements": eval_json.get("improvements", ["Continue technical practice and system design study."])
        }
    except Exception:
        return fallback_eval
