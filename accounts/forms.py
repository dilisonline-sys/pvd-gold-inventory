from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError

from .models import User, ROLES


class LoginForm(AuthenticationForm):
    """
    Standard login form using Django's built-in AuthenticationForm.
    Adds Bootstrap-friendly widget attributes.
    """

    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        }),
        label='Username',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        }),
        label='Password',
    )


class UserCreationForm(BaseUserCreationForm):
    """
    Form for creating a new user with all goldsmith-specific fields.
    Extends Django's built-in UserCreationForm (which handles password1/password2).
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='First Name',
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Last Name',
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Email Address',
    )
    role = forms.ChoiceField(
        choices=ROLES,
        initial='viewer',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Role',
    )
    employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Employee ID',
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Phone Number',
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Department',
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'role',
            'employee_id',
            'phone',
            'department',
            'password1',
            'password2',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to the password fields provided by BaseUserCreationForm
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with this email address already exists.')
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id', '').strip() or None
        if employee_id and User.objects.filter(employee_id=employee_id).exists():
            raise ValidationError('This Employee ID is already in use.')
        return employee_id


class UserEditForm(forms.ModelForm):
    """
    Form for editing an existing user's profile and role.
    Does NOT handle password changes (use Django's built-in password-change views).
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='First Name',
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Last Name',
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Email Address',
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'role',
            'employee_id',
            'phone',
            'department',
            'is_active',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('A user with this email address already exists.')
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id', '').strip() or None
        if employee_id:
            qs = User.objects.filter(employee_id=employee_id)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('This Employee ID is already in use.')
        return employee_id
