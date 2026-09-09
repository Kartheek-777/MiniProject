from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import StudentProfile

class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. karthik_cs'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@college.edu'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'At least 8 characters'}), required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter password'}), required=True)

    # Student Profile Specific Fields
    college = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. National Institute of Technology'}))
    degree = forms.CharField(max_length=100, required=False, initial='B.Tech', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech / B.E.'}))
    branch = forms.CharField(max_length=100, required=False, initial='Computer Science & Engineering', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}))
    graduation_year = forms.IntegerField(required=False, initial=2026, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2026'}))
    target_role = forms.CharField(max_length=150, required=False, initial='Software Engineer', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Engineer'}))
    cgpa = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 8.5'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            if 'form-control' not in existing:
                field.widget.attrs['class'] = f'form-control {existing}'.strip()


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', "Passwords do not match.")
            else:
                try:
                    validate_password(password1)
                except ValidationError as error:
                    self.add_error('password1', error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number'),
                college=self.cleaned_data.get('college') or 'Engineering Institute',
                degree=self.cleaned_data.get('degree') or 'B.Tech',
                branch=self.cleaned_data.get('branch') or 'Computer Science & Engineering',
                graduation_year=self.cleaned_data.get('graduation_year') or 2026,
                cgpa=self.cleaned_data.get('cgpa'),
                target_role=self.cleaned_data.get('target_role') or 'Software Engineer',
            )
        return user

class StudentProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = StudentProfile
        fields = [
            'profile_picture', 'phone_number', 'college', 'degree', 'branch',
            'graduation_year', 'cgpa', 'target_role', 'bio'
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'cgpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_role': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        if 'first_name' in self.cleaned_data:
            user.first_name = self.cleaned_data['first_name']
        if 'last_name' in self.cleaned_data:
            user.last_name = self.cleaned_data['last_name']
        if 'email' in self.cleaned_data:
            user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile

