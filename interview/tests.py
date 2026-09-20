from django.test import TestCase
from django.contrib.auth.models import User
from interview.models import MockInterviewSession, InterviewMessage
from interview.services import evaluate_interview_session, get_candidate_resume_context
from resume_analyzer.models import Resume

class InterviewEvaluationAndResumeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testcandidate', password='Password123')
        self.session = MockInterviewSession.objects.create(
            user=self.user,
            target_role='Electronics Engineer',
            interview_mode='Full Interview',
            current_phase='HR Screening',
            status='in_progress'
        )

    def test_zero_candidate_responses_evaluation(self):
        """Ending an interview session with 0 candidate responses must return 0.0/10 and No Hire."""
        history = self.session.messages.all()
        eval_data = evaluate_interview_session(self.session, history)

        self.assertEqual(eval_data['rating'], "0.0/10")
        self.assertEqual(eval_data['hire_decision'], "No Hire")
        self.assertEqual(eval_data['communication'], "Weak")
        self.assertIn("No candidate responses were recorded", eval_data['strengths'][0])

    def test_insufficient_candidate_responses_evaluation(self):
        """Candidate providing only 1 short answer ('hi') must return 1.5/10 and No Hire."""
        InterviewMessage.objects.create(
            session=self.session,
            sender='candidate',
            message='hi',
            round_name='HR Screening'
        )
        history = self.session.messages.all()
        eval_data = evaluate_interview_session(self.session, history)

        self.assertEqual(eval_data['rating'], "1.5/10")
        self.assertEqual(eval_data['hire_decision'], "No Hire")

    def test_no_resume_context_notice(self):
        """When user has no uploaded resume, context must state NO RESUME UPLOADED."""
        context = get_candidate_resume_context(self.user)
        self.assertIn("NO RESUME UPLOADED", context)
        self.assertIn("DO NOT invent or reference fake candidate projects", context)

    def test_uploaded_resume_context_integration(self):
        """When user uploads a resume, extracted skills & projects must be included in context."""
        Resume.objects.create(
            user=self.user,
            title='Embedded Systems Resume',
            extracted_skills=['ARM Cortex', 'Embedded C', 'RTOS', 'SPI/I2C'],
            extracted_projects=[{'name': 'Smart IoT Controller', 'details': 'STM32 based hardware design'}]
        )

        context = get_candidate_resume_context(self.user)
        self.assertIn("Embedded Systems Resume", context)
        self.assertIn("ARM Cortex", context)
        self.assertIn("Smart IoT Controller", context)
