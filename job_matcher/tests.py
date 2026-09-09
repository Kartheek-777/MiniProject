import tempfile, os, pymupdf
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from resume_analyzer.models import Resume
from job_matcher.models import JobMatch
from job_matcher.services import extract_skills_from_jd, compute_rule_match

class Phase5JobMatcherTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='student_job1', password='Password123!')
        self.user2 = User.objects.create_user(username='student_job2', password='Password123!')

        # Create resume for user1
        self.resume1 = Resume.objects.create(
            user=self.user1,
            title='Backend Python Resume',
            extracted_skills=['Python', 'Django', 'SQL', 'Git', 'REST API']
        )

    def test_skill_extraction_and_rule_match_math(self):
        jd_text = """
        We are looking for a Senior Software Engineer with strong expertise in Python, Django, Docker, AWS, and MySQL.
        Must have good experience with REST API development and Git version control.
        """
        jd_skills = extract_skills_from_jd(jd_text)
        self.assertIn('Python', jd_skills)
        self.assertIn('Django', jd_skills)
        self.assertIn('Docker', jd_skills)
        self.assertIn('AWS', jd_skills)

        rule_res = compute_rule_match(self.resume1.extracted_skills, jd_skills)
        self.assertIn('Python', rule_res['matched_skills'])
        self.assertIn('Django', rule_res['matched_skills'])
        self.assertIn('Docker', rule_res['missing_skills'])
        self.assertIn('AWS', rule_res['missing_skills'])
        self.assertGreater(rule_res['match_score'], 0)

    def test_job_match_creation_flow(self):
        self.client.login(username='student_job1', password='Password123!')
        response = self.client.post(reverse('job_match_create'), {
            'job_title': 'Python Backend Engineer',
            'company_name': 'TechCorp Solutions',
            'job_description': 'Require Python, Django, SQL, Docker, and AWS skills for full-stack API integration.',
            'resume': self.resume1.pk
        })
        self.assertEqual(response.status_code, 302)

        match = JobMatch.objects.get(user=self.user1, job_title='Python Backend Engineer')
        self.assertIn('Python', match.matched_skills)
        self.assertIn('Docker', match.missing_skills)
        self.assertGreater(match.match_score, 0)

        # Test Owner Detail View Access
        detail_res = self.client.get(reverse('job_match_detail', kwargs={'pk': match.pk}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Python Backend Engineer')

        # Test User Security Isolation (User 2 gets 404)
        self.client.login(username='student_job2', password='Password123!')
        unauthorized_res = self.client.get(reverse('job_match_detail', kwargs={'pk': match.pk}))
        self.assertEqual(unauthorized_res.status_code, 404)
