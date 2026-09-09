from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import landing_page
from accounts.views import ProfileView
from career.views import roadmap_view
from job_matcher.views import skill_gap_analytics_api, job_auto_apply_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing'),
    path('profile/', ProfileView.as_view(), name='profile_direct'),
    path('dashboard/roadmap/', roadmap_view, name='dashboard_roadmap'),
    path('jobs/auto-apply/', job_auto_apply_view, name='job_auto_apply_direct'),
    path('api/skill-gap-analytics/', skill_gap_analytics_api, name='api_skill_gap_analytics_direct'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('resume/', include('resume_analyzer.urls')),
    path('jobs/', include('job_matcher.urls')),
    path('career/', include('career.urls')),
    path('interview/', include('interview.urls')),
    path('ai/', include('ai_engine.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
