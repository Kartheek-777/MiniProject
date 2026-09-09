from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/generate-summary/', views.GenerateSummaryView.as_view(), name='generate_ai_summary'),
    path('google/login/', views.google_login_view, name='google_login'),
    path('google/select-account/', views.google_select_account_view, name='google_select_account'),
    path('google/login/callback/', views.google_callback_view, name='google_callback'),
    path('google/login/demo/', views.google_demo_login_view, name='google_demo'),
]
