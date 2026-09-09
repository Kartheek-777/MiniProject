from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('api/activity/', views.realtime_activity_api, name='realtime_activity_api'),
]



