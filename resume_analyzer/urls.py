from django.urls import path
from . import views

urlpatterns = [
    path('', views.resume_list, name='resume_index'),
    path('upload/', views.resume_upload, name='resume_upload'),
    path('<int:pk>/', views.resume_detail, name='resume_detail'),
    path('<int:pk>/reanalyze/', views.resume_reanalyze, name='resume_reanalyze'),
    path('<int:pk>/delete/', views.resume_delete, name='resume_delete'),
]
