from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json

from .models import CareerRoadmap
from placement_copilot.services.roadmap_engine import generate_career_roadmap
from accounts.models import StudentProfile
from resume_analyzer.models import Resume
from job_matcher.models import JobMatch

@login_required
def roadmap_view(request, pk=None):
    """
    Core Roadmap View handling:
    GET -> Renders current or latest CareerRoadmap for user.
    POST -> Generates a brand new AI Career Roadmap dynamically.
    """
    user = request.user
    profile, _ = StudentProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        custom_role = request.POST.get('target_role', '').strip() or profile.target_role
        roadmap = generate_career_roadmap(user, custom_target_role=custom_role)
        messages.success(request, f"Personalized AI Roadmap for '{roadmap.target_role}' generated successfully!")
        return redirect('dashboard_roadmap')

    # Fetch requested or latest roadmap
    if pk:
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=user)
    else:
        roadmap = CareerRoadmap.objects.filter(user=user).first()

    all_roadmaps = CareerRoadmap.objects.filter(user=user)

    # Gather Context Metrics
    latest_match = JobMatch.objects.filter(user=user).first()
    match_score = latest_match.match_score if latest_match else 0

    latest_resume = Resume.objects.filter(user=user).first()
    has_resume = bool(latest_resume)

    roadmap_phases = []
    if roadmap and roadmap.roadmap_json and isinstance(roadmap.roadmap_json, dict):
        roadmap_phases = roadmap.roadmap_json.get('roadmap', [])

    context = {
        'roadmap': roadmap,
        'roadmap_phases': roadmap_phases,
        'all_roadmaps': all_roadmaps,
        'profile': profile,
        'match_score': match_score,
        'has_resume': has_resume,
        'target_role': roadmap.target_role if roadmap else (profile.target_role or 'Software Engineer')
    }
    return render(request, 'career/roadmap.html', context)
