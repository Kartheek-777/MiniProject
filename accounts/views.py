from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db.models import Avg
from django.http import JsonResponse

from .models import StudentProfile
from .forms import StudentRegistrationForm, StudentProfileUpdateForm
from .services import generate_ai_profile_summary
from .google_auth import google_login_view, google_callback_view, google_demo_login_view, google_select_account_view
from resume_analyzer.models import Resume
from job_matcher.models import JobMatch
from interview.models import MockInterviewSession

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Registration successful for {user.username}! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct errors below.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard_home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@never_cache
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('landing')


class ProfileView(LoginRequiredMixin, View):
    """
    Class-Based View for rendering and updating the User Profile & Analytics Dashboard.
    """
    def get(self, request):
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        form = StudentProfileUpdateForm(instance=profile, user=request.user)

        # Real DB Analytics
        resumes_qs = Resume.objects.filter(user=request.user)
        resumes_count = resumes_qs.count()
        latest_resume = resumes_qs.first()

        ats_score = 0
        extracted_skills = []
        if latest_resume:
            extracted_skills = latest_resume.extracted_skills if isinstance(latest_resume.extracted_skills, list) else []
            skills_count = len(extracted_skills)
            ats_score = min(96, max(45, 40 + skills_count * 7)) if skills_count > 0 else 60

        job_matches_qs = JobMatch.objects.filter(user=request.user)
        job_match_avg = job_matches_qs.aggregate(Avg('match_score'))['match_score__avg']
        job_match_avg = round(job_match_avg) if job_match_avg is not None else 0
        last_job_match = job_matches_qs.first()

        interviews_qs = MockInterviewSession.objects.filter(user=request.user)
        completed_interviews = interviews_qs.filter(completed=True)
        
        interview_scores = []
        for session in completed_interviews:
            if session.evaluation_data and isinstance(session.evaluation_data, dict):
                r = str(session.evaluation_data.get('rating', ''))
                try:
                    val = float(r.split('/')[0]) if '/' in r else float(r)
                    interview_scores.append(val)
                except ValueError:
                    pass

        avg_interview_score = f"{round(sum(interview_scores)/len(interview_scores), 1)} / 10" if interview_scores else "N/A"
        latest_interview = interviews_qs.first()

        stats = {
            'resumes_count': resumes_count,
            'ats_score': ats_score,
            'job_match_avg': job_match_avg,
            'avg_interview_score': avg_interview_score,
            'skills': extracted_skills,
        }

        context = {
            'profile': profile,
            'form': form,
            'stats': stats,
            'completeness': profile.completion_percentage,
            'missing_fields': profile.missing_fields,
            'recent_resumes': resumes_qs[:3],
            'latest_resume': latest_resume,
            'last_job_match': last_job_match,
            'latest_interview': latest_interview,
        }
        return render(request, 'accounts/profile.html', context)

    def post(self, request):
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        form = StudentProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Error updating profile. Please check the form fields.")
            return self.get(request)


class GenerateSummaryView(LoginRequiredMixin, View):
    """
    Class-Based View API endpoint returning strictly JSON response with Gemini AI summary.
    """
    def post(self, request):
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)

        resumes_qs = Resume.objects.filter(user=request.user)
        resumes_count = resumes_qs.count()
        latest_resume = resumes_qs.first()
        extracted_skills = latest_resume.extracted_skills if (latest_resume and isinstance(latest_resume.extracted_skills, list)) else []

        job_match_avg = JobMatch.objects.filter(user=request.user).aggregate(Avg('match_score'))['match_score__avg'] or 0

        interviews = MockInterviewSession.objects.filter(user=request.user, completed=True)
        scores = []
        for s in interviews:
            r = str(s.evaluation_data.get('rating', ''))
            try:
                val = float(r.split('/')[0]) if '/' in r else float(r)
                scores.append(val)
            except Exception:
                pass
        avg_int = f"{round(sum(scores)/len(scores), 1)}/10" if scores else "N/A"

        stats = {
            'resumes_count': resumes_count,
            'job_match_avg': round(job_match_avg),
            'avg_interview_score': avg_int,
            'skills': extracted_skills,
        }

        # Force refresh summary via Gemini API
        summary = generate_ai_profile_summary(request.user, profile, stats, force_refresh=True)

        return JsonResponse({
            "status": "success",
            "summary": summary,
            "bio": summary
        })
