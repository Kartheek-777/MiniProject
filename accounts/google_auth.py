import secrets
import urllib.parse
import re
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from .models import StudentProfile


def is_google_oauth_configured():
    """Check if Google OAuth Client ID and Secret are configured in settings."""
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()
    placeholders = ['your_google_client_id_here', 'your_google_client_secret_here', '']
    return bool(client_id and client_secret and client_id not in placeholders and client_secret not in placeholders)


def google_login_view(request):
    """
    Initiate Google OAuth 2.0 Authorization Flow.
    Renders the exact Google Account Chooser screen if GOOGLE_CLIENT_ID is not configured in .env,
    or redirects to accounts.google.com if a live Client ID is present.
    """
    if not is_google_oauth_configured():
        return render(request, 'accounts/google_account_chooser.html', {'hide_auth_nav_links': True})

    client_id = settings.GOOGLE_CLIENT_ID.strip()
    state = secrets.token_hex(16)
    request.session['google_oauth_state'] = state
    request.session['google_next_url'] = request.GET.get('next', '')

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    }

    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(url)


def google_select_account_view(request):
    """
    Handle Google Account selection from the Account Chooser UI.
    Authenticates or registers the candidate and logs them into PlacementCopilot.
    """
    if request.method != 'POST':
        return redirect('google_login')

    email = request.POST.get('email', '').strip().lower()
    full_name = request.POST.get('full_name', '').strip()

    if not email:
        messages.error(request, "Please enter or select a valid Google email.")
        return redirect('google_login')

    # Split name into first and last
    name_parts = full_name.split(' ', 1) if full_name else []
    first_name = name_parts[0] if len(name_parts) > 0 else email.split('@')[0].capitalize()
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    user = User.objects.filter(email__iexact=email).first()
    is_new = False

    if not user:
        is_new = True
        base_username = re.sub(r'[^a-zA-Z0-9_]', '_', email.split('@')[0])
        if not base_username:
            base_username = 'google_user'

        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_unusable_password()
        user.save()

    StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'college': 'Engineering Institute',
            'degree': 'B.Tech',
            'branch': 'Computer Science & Engineering',
            'graduation_year': 2026,
            'target_role': 'Software Engineer',
            'bio': 'Candidate authenticated via Google Single Sign-On (SSO).',
        }
    )

    login(request, user)

    if is_new:
        messages.success(request, f"Welcome to PlacementCopilot, {user.first_name or user.username}! Registered via Google ({email}).")
    else:
        messages.success(request, f"Signed in as {user.get_full_name() or user.username} ({email}) via Google.")

    next_url = request.session.pop('google_next_url', None)
    if next_url:
        return redirect(next_url)
    return redirect('dashboard_home')


def google_callback_view(request):
    """
    Handle OAuth callback from Google.
    Exchanges code for tokens, retrieves user profile, creates/authenticates Django user.
    """
    error = request.GET.get('error')
    if error:
        messages.error(request, f"Google authentication was cancelled or failed: {error}")
        return redirect('login')

    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.get('google_oauth_state')

    if not code or not state or state != saved_state:
        messages.error(request, "Invalid OAuth security state token. Please try again.")
        return redirect('login')

    # Clean up state token
    request.session.pop('google_oauth_state', None)

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    token_url = 'https://oauth2.googleapis.com/token'

    token_payload = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    try:
        token_response = requests.post(token_url, data=token_payload, timeout=12)
        if token_response.status_code != 200:
            if settings.DEBUG:
                return google_demo_login_view(request)
            messages.error(request, f"Failed to retrieve access token from Google: {token_response.text}")
            return redirect('login')

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # Fetch User Information
        userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=headers, timeout=12)

        if userinfo_response.status_code != 200:
            messages.error(request, "Failed to retrieve user profile from Google.")
            return redirect('login')

        user_info = userinfo_response.json()
        email = user_info.get('email', '').strip().lower()
        given_name = user_info.get('given_name', '')
        family_name = user_info.get('family_name', '')

        if not email:
            messages.error(request, "Google account did not return a valid email address.")
            return redirect('login')

        # Check if user already exists
        user = User.objects.filter(email__iexact=email).first()
        is_new_user = False

        if not user:
            is_new_user = True
            # Generate clean, unique username
            base_username = re.sub(r'[^a-zA-Z0-9_]', '_', email.split('@')[0])
            if not base_username:
                base_username = 'google_user'
            
            username = base_username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=given_name,
                last_name=family_name
            )
            user.set_unusable_password()
            user.save()

        # Ensure StudentProfile exists
        StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'college': 'Engineering Institute',
                'degree': 'B.Tech',
                'branch': 'Computer Science & Engineering',
                'graduation_year': 2026,
                'target_role': 'Software Engineer',
            }
        )

        # Authenticate user with Django Session
        login(request, user)

        if is_new_user:
            messages.success(request, f"Welcome to PlacementCopilot, {user.first_name or user.username}! Your account has been registered via Google.")
        else:
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}! Successfully logged in with Google.")

        next_url = request.session.pop('google_next_url', None)
        if next_url:
            return redirect(next_url)
        return redirect('dashboard_home')

    except Exception as e:
        messages.error(request, f"An error occurred during Google authentication: {str(e)}")
        return redirect('login')


def google_demo_login_view(request):
    """
    Demo/Sandbox Google Sign-In for testing without live Google API keys in DEBUG mode.
    """
    if not settings.DEBUG:
        messages.error(request, "Demo Google sign-in is only available in DEBUG mode.")
        return redirect('login')

    email = "alex.rivera.google@example.com"
    user = User.objects.filter(email=email).first()

    if not user:
        user = User.objects.create_user(
            username="alex_rivera_google",
            email=email,
            first_name="Alex",
            last_name="Rivera"
        )
        user.set_unusable_password()
        user.save()

    StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'college': 'Stanford Institute of Technology',
            'degree': 'B.Tech',
            'branch': 'Computer Science & Engineering',
            'graduation_year': 2026,
            'target_role': 'AI / Software Engineer',
            'bio': 'Passionate candidate authenticated via Google Single Sign-On (SSO).',
        }
    )

    login(request, user)
    messages.success(request, "Google OAuth Demo Sign-In Successful! Authenticated as Alex Rivera.")
    return redirect('dashboard_home')
