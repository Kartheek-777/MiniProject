from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from career.models import CareerRoadmap
from career.services import generate_career_roadmap_ai

class Phase6CareerRoadmapTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='career_student1', password='Password123!')
        self.user2 = User.objects.create_user(username='career_student2', password='Password123!')

    def test_roadmap_ai_service_structure(self):
        roadmap_json = generate_career_roadmap_ai(
            target_role='Software Development Engineer',
            current_skills=['Python', 'Django', 'SQL'],
            missing_skills=['Docker', 'AWS', 'System Design']
        )
        self.assertIsInstance(roadmap_json, dict)
        self.assertIn('roadmap', roadmap_json)
        self.assertGreater(len(roadmap_json['roadmap']), 0)
        
        week1 = roadmap_json['roadmap'][0]
        self.assertIn('phase', week1)
        self.assertIn('skills', week1)
        self.assertIn('milestone', week1)

    def test_career_roadmap_creation_flow(self):
        self.client.login(username='career_student1', password='Password123!')
        response = self.client.post(reverse('career_create'), {
            'title': 'SDE 90-Day Acceleration Roadmap',
            'target_role': 'Software Development Engineer',
            'manual_missing_skills': 'Docker, AWS, System Design'
        })
        self.assertEqual(response.status_code, 302)

        roadmap = CareerRoadmap.objects.get(user=self.user1, target_role='Software Development Engineer')
        self.assertIn('Software Development Engineer', roadmap.title)
        self.assertIn('Docker', roadmap.missing_skills)

        # Test Owner Detail View Access
        detail_res = self.client.get(reverse('career_detail', kwargs={'pk': roadmap.pk}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Software Development Engineer')

        # Test User Security Isolation (User 2 gets 404)
        self.client.login(username='career_student2', password='Password123!')
        unauthorized_res = self.client.get(reverse('career_detail', kwargs={'pk': roadmap.pk}))
        self.assertEqual(unauthorized_res.status_code, 404)
