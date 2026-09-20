from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
import json

from .models import MockInterviewSession, InterviewMessage
from .forms import StartInterviewForm
from .services import generate_interviewer_response, evaluate_interview_session

@login_required
def index(request):
    sessions = MockInterviewSession.objects.filter(user=request.user).order_by('-started_at')
    form = StartInterviewForm()
    
    active_resume = None
    try:
        from resume_analyzer.models import Resume
        active_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    except Exception:
        pass

    return render(request, 'interview/index.html', {
        'sessions': sessions,
        'form': form,
        'active_resume': active_resume
    })

@login_required
def start_interview(request):
    if request.method == 'POST':
        form = StartInterviewForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.status = 'in_progress'
            session.current_phase = 'HR Screening'
            session.save()

            # Create opening question turn
            initial_q = f"Welcome to your AI Technical Mock Interview for the '{session.target_role}' position. Let's begin with Phase 1: HR Screening. Tell me about yourself, your background, and why you are targeting this role?"
            
            InterviewMessage.objects.create(
                session=session,
                sender='interviewer',
                message=initial_q,
                round_name='HR Screening'
            )

            messages.success(request, f"Mock Interview Session started! Role: {session.target_role}")
            return redirect('interview_room', pk=session.pk)
    return redirect('interview_index')

@login_required
def interview_room(request, pk):
    session = get_object_or_404(MockInterviewSession, pk=pk, user=request.user)
    if session.status == 'completed':
        return redirect('interview_scorecard', pk=session.pk)

    active_resume = None
    try:
        from resume_analyzer.models import Resume
        active_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    except Exception:
        pass

    chat_messages = session.messages.all()
    return render(request, 'interview/room.html', {
        'session': session,
        'chat_messages': chat_messages,
        'active_resume': active_resume
    })

@login_required
def send_message(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    session = get_object_or_404(MockInterviewSession, pk=pk, user=request.user)
    if session.status == 'completed':
        return JsonResponse({'error': 'Session already completed'}, status=400)

    # Handle body JSON or POST data
    user_msg_text = request.POST.get('message', '').strip()
    if not user_msg_text and request.body:
        try:
            body = json.loads(request.body)
            user_msg_text = body.get('message', '').strip()
        except Exception:
            pass

    if not user_msg_text:
        return JsonResponse({'error': 'Message content cannot be empty'}, status=400)

    # Save Candidate message
    cand_msg = InterviewMessage.objects.create(
        session=session,
        sender='candidate',
        message=user_msg_text,
        round_name=session.current_phase
    )

    # Get history up to now
    history = list(session.messages.all())

    # Query AI Engine for interviewer turn
    ai_turn = generate_interviewer_response(session, history, user_msg_text)

    # Update phase if shifted
    if ai_turn['detected_phase'] and ai_turn['detected_phase'] != session.current_phase:
        session.current_phase = ai_turn['detected_phase']
        session.save()

    # Save Interviewer message
    interviewer_msg = InterviewMessage.objects.create(
        session=session,
        sender='interviewer',
        message=ai_turn['message'],
        round_name=session.current_phase
    )

    return JsonResponse({
        'success': True,
        'candidate_message': {
            'text': cand_msg.message,
            'time': cand_msg.created_at.strftime('%H:%M')
        },
        'interviewer_message': {
            'text': interviewer_msg.message,
            'phase': interviewer_msg.round_name,
            'time': interviewer_msg.created_at.strftime('%H:%M')
        },
        'current_phase': session.current_phase,
        'is_complete': ai_turn.get('is_complete', False)
    })

@login_required
def end_interview(request, pk):
    if request.method != 'POST':
        return redirect('interview_index')

    session = get_object_or_404(MockInterviewSession, pk=pk, user=request.user)
    
    if session.status != 'completed':
        history = session.messages.all()
        eval_data = evaluate_interview_session(session, history)
        
        session.status = 'completed'
        session.completed = True
        session.completed_at = timezone.now()
        session.evaluation_data = eval_data
        session.save()
        messages.success(request, "Interview completed successfully! Evaluation report generated.")

    return redirect('interview_scorecard', pk=session.pk)

@login_required
def interview_scorecard(request, pk):
    session = get_object_or_404(MockInterviewSession, pk=pk, user=request.user)
    if not session.completed or not session.evaluation_data:
        # Generate on the fly if needed
        history = session.messages.all()
        eval_data = evaluate_interview_session(session, history)
        session.status = 'completed'
        session.completed = True
        session.completed_at = timezone.now()
        session.evaluation_data = eval_data
        session.save()

    return render(request, 'interview/scorecard.html', {
        'session': session,
        'eval': session.evaluation_data
    })
