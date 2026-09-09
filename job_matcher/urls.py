from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_index'),
    path('create/', views.job_match_create, name='job_match_create'),
    path('<int:pk>/', views.job_match_detail, name='job_match_detail'),
    path('analytics/', views.skill_gap_analytics_view, name='skill_gap_analytics'),
    path('api/skill-gap-analytics/', views.skill_gap_analytics_api, name='skill_gap_analytics_api'),
    path('auto-apply/', views.job_auto_apply_view, name='job_auto_apply'),
    path('apply/<int:job_id>/', views.generate_apply_assist_api, name='generate_apply_assist'),
]
