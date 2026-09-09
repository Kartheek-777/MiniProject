from django.test import TestCase
from ai_engine.services import analyze_resume_with_ai, FALLBACK_AI_ANALYSIS
from resume_analyzer.models import Resume
from django.contrib.auth.models import User

class Phase4AIEngineTests(TestCase):
    def setUp(self):
        self.sample_text = """
        Rahul Sharma
        Email: rahul@engineering.edu
        Skills: Python, Django, SQL, Git, Data Structures
        Experience: 2 years software engineering internship
        Projects: Built an E-Commerce platform using Django and React.
        """

    def test_ai_service_fallback_on_unconfigured_key(self):
        # Without GEMINI_API_KEY, should safely return fallback dict without throwing exceptions
        result = analyze_resume_with_ai(self.sample_text)
        self.assertIsInstance(result, dict)
        self.assertIn("skills", result)
        self.assertIn("experience_level", result)
        self.assertIn("strengths", result)
        self.assertIn("weaknesses", result)
        self.assertIn("missing_skills", result)
        self.assertIn("suggestions", result)

    def test_ai_service_empty_input_handling(self):
        result = analyze_resume_with_ai("")
        self.assertEqual(result["experience_level"], "Unknown")
        self.assertIn("Empty or invalid resume text provided.", result["weaknesses"])

    def test_resume_model_ai_analysis_field(self):
        user = User.objects.create_user(username='aitestuser', password='Password123!')
        ai_data = {
            "skills": ["Python", "Django", "SQL"],
            "experience_level": "Beginner (0–1 years/student)",
            "strengths": ["Strong Django backend foundation", "Good project experience"],
            "weaknesses": ["Needs more system design exposure"],
            "missing_skills": ["Docker", "Kubernetes", "AWS"],
            "suggestions": ["Add containerization to projects", "Build REST APIs"]
        }
        resume = Resume.objects.create(
            user=user,
            title='AI Analyzed Resume',
            extracted_text=self.sample_text,
            ai_analysis=ai_data
        )
        self.assertEqual(resume.ai_analysis["experience_level"], "Beginner (0–1 years/student)")
        self.assertEqual(len(resume.ai_analysis["skills"]), 3)
        self.assertIn("Docker", resume.ai_analysis["missing_skills"])
