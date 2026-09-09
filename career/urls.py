from django.urls import path
from . import views

urlpatterns = [
    path('', views.roadmap_view, name='career_index'),
    path('generate/', views.roadmap_view, name='career_create'),
    path('<int:pk>/', views.roadmap_view, name='career_detail'),
]
