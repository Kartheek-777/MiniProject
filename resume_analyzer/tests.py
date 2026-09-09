import os
import tempfile
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import Resume
from .services import parse_resume_data, extract_text_from_pdf
import pymupdf

class Phase3ResumeUploadAndParsingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='student1', password='Password123!')
        self.user2 = User.objects.create_user(username='student2', password='Password123!')

    def test_parser_service_logic(self):
        sample_text = """
        Karthik Sharma
        Email: karthik.sharma@example.com
        Phone: +91 9876543210

        Education:
        B.Tech in Computer Science & Engineering from National Institute of Technology, CGPA: 8.75

        Technical Skills:
        Python, Java, C++, Django, SQL, MySQL, Git, Data Structures, Algorithms, Docker, AWS

        Projects:
        1. AI Placement Intelligence & Career Copilot web app built using Django and MySQL.
        2. E-Commerce Microservices Engine built with Python and Docker.
        """

        parsed = parse_resume_data(sample_text)
        self.assertEqual(parsed['email'], 'karthik.sharma@example.com')
        self.assertIn('Python', parsed['skills'])
        self.assertIn('Django', parsed['skills'])
        self.assertIn('MySQL', parsed['skills'])
        self.assertIn('Data Structures', parsed['skills'])
        self.assertTrue(any('B.Tech' in edu for edu in parsed['education']))
        self.assertTrue(any('Placement Intelligence' in proj for proj in parsed['projects']))

    def test_pdf_extraction_and_upload_flow(self):
        # Generate a temporary valid PDF in memory using PyMuPDF
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_pdf_path = temp_pdf.name
        temp_pdf.close()  # Close handle so PyMuPDF can write to it on Windows

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 50), "John Doe\nEmail: john.doe@engineering.edu\nSkills: Python, Django, SQL, Git\nEducation: B.Tech in CSE")
        doc.save(temp_pdf_path)
        doc.close()

        try:
            self.client.login(username='student1', password='Password123!')

            with open(temp_pdf_path, 'rb') as pdf_file:
                uploaded_pdf = SimpleUploadedFile("my_resume.pdf", pdf_file.read(), content_type="application/pdf")
                response = self.client.post(reverse('resume_upload'), {
                    'title': 'John SDE Resume',
                    'file': uploaded_pdf
                })

            self.assertEqual(response.status_code, 302)  # Redirects to detail page on success

            # Verify Resume in DB
            resume = Resume.objects.get(user=self.user1, title='John SDE Resume')
            self.assertEqual(resume.extracted_email, 'john.doe@engineering.edu')
            self.assertIn('Python', resume.extracted_skills)
            self.assertIn('Django', resume.extracted_skills)

            # Verify detail view access for owner
            detail_res = self.client.get(reverse('resume_detail', kwargs={'pk': resume.pk}))
            self.assertEqual(detail_res.status_code, 200)
            self.assertContains(detail_res, 'john.doe@engineering.edu')

            # Verify security: User 2 cannot access User 1's resume
            self.client.login(username='student2', password='Password123!')
            unauthorized_res = self.client.get(reverse('resume_detail', kwargs={'pk': resume.pk}))
            self.assertEqual(unauthorized_res.status_code, 404)

        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
