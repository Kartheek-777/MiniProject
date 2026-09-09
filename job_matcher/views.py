from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import JobMatch, JobListing, ApplicationAssist
from .forms import JobMatchForm
from .services import extract_skills_from_jd, compute_rule_match, analyze_job_match_with_ai
from ai_engine.skill_gap_analyzer import analyze_skill_gap_progress
from ai_engine.apply_assistant import evaluate_candidate_job_matches, generate_apply_assist

@login_required
def job_list(request):
    matches = JobMatch.objects.filter(user=request.user)
    return render(request, 'job_matcher/list.html', {'matches': matches})

@login_required
def job_match_create(request):
    if request.method == 'POST':
        form = JobMatchForm(request.POST, user=request.user)
        if form.is_valid():
            job_match = form.save(commit=False)
            job_match.user = request.user
            
            resume = form.cleaned_data['resume']
            job_text = form.cleaned_data['job_description']
            job_title = form.cleaned_data['job_title']

            # 1. Rule-Based Skill Extraction & Overlap Computation
            jd_skills = extract_skills_from_jd(job_text)
            rule_result = compute_rule_match(resume.extracted_skills or [], jd_skills)

            job_match.match_score = rule_result['match_score']
            job_match.matched_skills = rule_result['matched_skills']

            # 2. AI Gemini Contextual Fit Analysis
            ai_insights = analyze_job_match_with_ai(
                resume_text=resume.extracted_text or "",
                job_title=job_title,
                job_description=job_text
            )

            job_match.fit_level = ai_insights['fit_level']
            job_match.match_summary = ai_insights['match_summary']
            job_match.recommendations = ai_insights['recommendations']

            # Combine rule missing skills + AI additional missing skills
            combined_missing = set(rule_result['missing_skills'])
            for add_skill in ai_insights.get('additional_missing_skills', []):
                combined_missing.add(add_skill)
            job_match.missing_skills = sorted(list(combined_missing))

            job_match.save()

            messages.success(request, f"Job Match evaluated for '{job_title}' with {job_match.match_score}% skill overlap!")
            return redirect('job_match_detail', pk=job_match.pk)
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        form = JobMatchForm(user=request.user)

    return render(request, 'job_matcher/input.html', {'form': form})

@login_required
def job_match_detail(request, pk):
    match_eval = get_object_or_404(JobMatch, pk=pk, user=request.user)
    context = {
        'match': match_eval,
        'matched_count': len(match_eval.matched_skills) if match_eval.matched_skills else 0,
        'missing_count': len(match_eval.missing_skills) if match_eval.missing_skills else 0,
    }
    return render(request, 'job_matcher/detail.html', context)

@login_required
def skill_gap_analytics_api(request):
    """
    API Endpoint GET /api/skill-gap-analytics/ returning JSON payload for Chart.js and AI Insights.
    """
    data = analyze_skill_gap_progress(request.user)
    return JsonResponse(data)

@login_required
def skill_gap_analytics_view(request):
    """
    HTML View rendering the Skill Gap Analytics Dashboard page with Chart.js charts.
    """
    initial_analytics = analyze_skill_gap_progress(request.user)
    return render(request, 'job_matcher/analytics.html', {
        'analytics': initial_analytics
    })

@login_required
def job_auto_apply_view(request):
    """
    Renders the AI Job Auto-Apply Assistant dashboard (/jobs/listings/ or /jobs/auto-apply/).
    Matches candidate skills against active job listings, ranks by match score %,
    and highlights top recommendations.
    """
    job_matches = evaluate_candidate_job_matches(request.user)
    top_recommendation_id = job_matches[0].job.id if job_matches else None

    return render(request, 'job_matcher/jobs.html', {
        'job_matches': job_matches,
        'top_recommendation_id': top_recommendation_id,
    })

@login_required
def generate_apply_assist_api(request, job_id):
    """
    Endpoint /jobs/apply/<job_id>/ returning JSON containing AI-generated Cover Letter and Resume Tips.
    """
    job = get_object_or_404(JobListing, pk=job_id)
    assist = generate_apply_assist(request.user, job)

    return JsonResponse({
        "success": True,
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "location": job.location,
        "apply_link": job.apply_link,
        "cover_letter": assist.cover_letter,
        "suggestions": assist.suggestions if isinstance(assist.suggestions, list) else []
    })
