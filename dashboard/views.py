from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Avg

from accounts.models import StudentProfile
from resume_analyzer.models import Resume
from job_matcher.models import JobMatch
from career.models import CareerRoadmap
from interview.models import MockInterviewSession

def landing_page(request):
    return render(request, 'landing.html')

@login_required
@never_cache
def dashboard_home(request):
    user = request.user
    profile, _ = StudentProfile.objects.get_or_create(user=user)

    # 1. Resume Analyzer Metrics
    resumes_qs = Resume.objects.filter(user=user)
    resumes_count = resumes_qs.count()
    latest_resume = resumes_qs.first()
    
    ats_score = None
    if latest_resume:
        skills_count = len(latest_resume.extracted_skills) if isinstance(latest_resume.extracted_skills, list) else 0
        ats_score = min(96, max(45, 40 + skills_count * 7)) if skills_count > 0 else 60

    # 2. Job Matcher Metrics
    job_matches_qs = JobMatch.objects.filter(user=user)
    job_match_avg = job_matches_qs.aggregate(Avg('match_score'))['match_score__avg']
    job_match_avg = round(job_match_avg) if job_match_avg is not None else None
    latest_job_match = job_matches_qs.first()

    # 3. Career Roadmap Metrics
    roadmaps_qs = CareerRoadmap.objects.filter(user=user)
    roadmaps_count = roadmaps_qs.count()
    latest_roadmap = roadmaps_qs.first()

    # Aggregate Skill Gaps Tracked
    skill_gaps = set()
    if latest_job_match and isinstance(latest_job_match.missing_skills, list):
        skill_gaps.update(latest_job_match.missing_skills)
    if latest_roadmap and isinstance(latest_roadmap.missing_skills, list):
        skill_gaps.update(latest_roadmap.missing_skills)
    
    skill_gaps_count = len(skill_gaps)

    # 4. Mock Interview Metrics
    interviews_qs = MockInterviewSession.objects.filter(user=user)
    mock_interviews_count = interviews_qs.count()
    latest_interview = interviews_qs.first()

    # Modules metadata for cards
    modules = [
        {
            'name': 'Resume Analyzer',
            'icon': 'bi-file-earmark-text',
            'url': 'resume_index',
            'desc': 'Upload & evaluate ATS resume score, extract technical skills',
            'count_label': f"{resumes_count} Uploaded" if resumes_count else "No resumes",
            'status_badge': f"{ats_score}% ATS Score" if ats_score else "Get Score"
        },
        {
            'name': 'Job Matcher',
            'icon': 'bi-briefcase',
            'url': 'job_index',
            'desc': 'Match candidate skills with target job descriptions & identify gaps',
            'count_label': f"{job_matches_qs.count()} Matches" if job_matches_qs.exists() else "No matches",
            'status_badge': f"{job_match_avg}% Avg Match" if job_match_avg else "Calculate Match"
        },
        {
            'name': 'Career Roadmap',
            'icon': 'bi-signpost-split',
            'url': 'career_index',
            'desc': 'Generate personalized 3-month AI learning paths for target role',
            'count_label': f"{roadmaps_count} Roadmaps" if roadmaps_count else "No roadmaps",
            'status_badge': f"{skill_gaps_count} Gaps Tracked" if skill_gaps_count else "Build Roadmap"
        },
        {
            'name': 'Mock Interview',
            'icon': 'bi-mic',
            'url': 'interview_index',
            'desc': 'Practice multi-round AI technical & HR questions under pressure',
            'count_label': f"{mock_interviews_count} Sessions" if mock_interviews_count else "No sessions",
            'status_badge': f"Phase {latest_interview.current_phase}" if latest_interview else "Start Simulation"
        },
    ]

    # Calculate Overall Placement Readiness Score Index
    base_ats = ats_score or 60
    base_match = job_match_avg or 60
    base_profile = profile.completion_percentage or 70
    readiness_score = min(98, max(45, round(base_ats * 0.4 + base_match * 0.3 + base_profile * 0.2 + min(10, mock_interviews_count * 5))))

    context = {
        'student_name': user.get_full_name() or user.username,
        'profile': profile,
        'completion_status': profile.completion_percentage,
        'readiness_score': readiness_score,
        'missing_fields': profile.missing_fields,
        'ats_score': ats_score,
        'job_match_avg': job_match_avg,
        'skill_gaps_count': skill_gaps_count,
        'mock_interviews_count': mock_interviews_count,
        'recent_resumes': resumes_qs[:3],
        'latest_resume': latest_resume,
        'latest_job_match': latest_job_match,
        'latest_roadmap': latest_roadmap,
        'latest_interview': latest_interview,
        'modules': modules
    }
    return render(request, 'dashboard/index.html', context)


from django.http import JsonResponse
from django.utils import timezone
import random

@login_required
def realtime_activity_api(request):

    user = request.user

    resumes_qs = Resume.objects.filter(user=user)
    job_matches_qs = JobMatch.objects.filter(user=user)
    interviews_qs = MockInterviewSession.objects.filter(user=user)
    roadmaps_qs = CareerRoadmap.objects.filter(user=user)
    
    events = []
    latest_resume = resumes_qs.first()
    if latest_resume:
        events.append({
            'title': f'Resume "{latest_resume.filename}" ATS Evaluated',
            'detail': f'{len(latest_resume.extracted_skills) if isinstance(latest_resume.extracted_skills, list) else 0} skills indexed in profile.',
            'time': latest_resume.uploaded_at.strftime('%H:%M'),
            'badge': 'Resume',
            'badge_cls': 'bg-danger'
        })
        
    latest_match = job_matches_qs.first()
    if latest_match:
        events.append({
            'title': f'Job Match: {latest_match.job_title}',
            'detail': f'Score: {latest_match.match_score}% ({latest_match.fit_level})',
            'time': latest_match.created_at.strftime('%H:%M'),
            'badge': 'Match',
            'badge_cls': 'bg-warning text-dark'
        })
        
    latest_interview = interviews_qs.first()
    if latest_interview:
        events.append({
            'title': f'Mock Interview Room ({latest_interview.target_role})',
            'detail': f'Current Phase: {latest_interview.current_phase}',
            'time': latest_interview.started_at.strftime('%H:%M'),
            'badge': 'Interview',
            'badge_cls': 'bg-info text-dark'
        })
        
    latest_roadmap = roadmaps_qs.first()
    if latest_roadmap:
        events.append({
            'title': f'Career Roadmap ({latest_roadmap.target_role})',
            'detail': f'Level: {latest_roadmap.difficulty_level}',
            'time': latest_roadmap.created_at.strftime('%H:%M'),
            'badge': 'Roadmap',
            'badge_cls': 'bg-success'
        })

    tips = [
        "Gemini AI Tip: Quantify achievements in your resume (e.g. 'Boosted performance by 25%') for high ATS ranking.",
        "Real-Time Alert: Fast-API, Docker, and PyTorch are top skill gaps requested by modern product tech teams.",
        "Interview Copilot: Structure system design answers using the STAR format (Situation, Task, Action, Result).",
        "Career Radar: Complete your mock interview rounds to unlock detailed technical competency ratings."
    ]

    return JsonResponse({
        'status': 'online',
        'timestamp': timezone.now().strftime('%H:%M:%S'),
        'events': events,
        'live_tip': random.choice(tips),
        'total_resumes': resumes_qs.count(),
        'total_job_matches': job_matches_qs.count(),
        'total_interviews': interviews_qs.count()
    })

