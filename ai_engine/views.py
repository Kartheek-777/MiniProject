from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def status_view(request):
    context = {
        'module_name': 'AI Engine Pipeline (Phase 1 Ready)',
        'status': 'Modular architecture configured. LLM provider integration scheduled for subsequent phases.'
    }
    return render(request, 'ai_engine/status.html', context)
