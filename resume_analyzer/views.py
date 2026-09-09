import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Resume
from .forms import ResumeUploadForm
from .services import extract_text_from_pdf, parse_resume_data
from ai_engine.services import analyze_resume_with_ai

@login_required
def resume_list(request):
    resumes = Resume.objects.filter(user=request.user)
    return render(request, 'resume_analyzer/list.html', {'resumes': resumes})

@login_required
def resume_upload(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            if not resume.title:
                resume.title = form.cleaned_data['file'].name
            resume.save()

            # Execute Phase 3 PDF Text Extraction & Rule-based Parsing
            try:
                raw_text = extract_text_from_pdf(resume.file.path)
                parsed_data = parse_resume_data(raw_text)

                resume.extracted_text = raw_text
                resume.extracted_email = parsed_data['email']
                resume.extracted_skills = parsed_data['skills']
                resume.extracted_education = parsed_data['education']
                resume.extracted_projects = parsed_data['projects']

                # Execute Phase 4 Gemini AI Resume Analysis
                ai_insights = analyze_resume_with_ai(raw_text)
                resume.ai_analysis = ai_insights
                resume.save()

                messages.success(request, f"Resume '{resume.title}' uploaded, parsed, and analyzed with AI successfully!")
                return redirect('resume_detail', pk=resume.pk)
            except Exception as e:
                messages.error(request, f"File saved, but processing failed: {str(e)}")
                return redirect('resume_detail', pk=resume.pk)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ResumeUploadForm()

    return render(request, 'resume_analyzer/upload.html', {'form': form})

@login_required
def resume_detail(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    context = {
        'resume': resume,
        'basic_skills_count': len(resume.extracted_skills) if resume.extracted_skills else 0,
        'ai_analysis': resume.ai_analysis or {},
    }
    return render(request, 'resume_analyzer/detail.html', context)

@login_required
def resume_reanalyze(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if resume.extracted_text:
        ai_insights = analyze_resume_with_ai(resume.extracted_text)
        resume.ai_analysis = ai_insights
        resume.save()
        messages.success(request, "AI Resume Analysis refreshed successfully!")
    else:
        messages.warning(request, "No extracted text available for AI analysis.")
    return redirect('resume_detail', pk=resume.pk)

@login_required
def resume_delete(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        title = resume.title
        # Clean up physical file on disk
        if resume.file and os.path.exists(resume.file.path):
            try:
                os.remove(resume.file.path)
            except Exception:
                pass
        resume.delete()
        messages.success(request, f"Resume '{title}' deleted successfully!")
        
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('resume_index')

    return redirect('resume_detail', pk=resume.pk)

