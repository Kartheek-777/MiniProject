from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='interview_index'),
    path('start/', views.start_interview, name='start_interview'),
    path('<int:pk>/', views.interview_room, name='interview_room'),
    path('<int:pk>/send/', views.send_message, name='send_message'),
    path('<int:pk>/end/', views.end_interview, name='end_interview'),
    path('<int:pk>/scorecard/', views.interview_scorecard, name='interview_scorecard'),
]
