from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import admin_required
from .forms import LoginForm, UserCreationForm, UserEditForm
from .models import User


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_view(request):
    """
    Display and process the login form.

    On GET  – render the blank login form.
    On POST – validate credentials; on success redirect to ``next`` param or
              the default LOGIN_REDIRECT_URL; on failure re-render with errors.
    """
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or '/'
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Log the current user out and redirect to the login page.
    Accepts both GET and POST to be forgiving of simple link-based logouts.
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------

@admin_required
def user_list(request):
    """
    Display a paginated list of all users in the system.
    Accessible to Administrators only.
    """
    users = User.objects.all().order_by('username')
    context = {
        'users': users,
        'title': 'User Management',
    }
    return render(request, 'accounts/user_list.html', context)


@admin_required
def user_create(request):
    """
    Create a new user account.
    Accessible to Administrators only.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'User "{user.username}" has been created successfully.',
            )
            return redirect('accounts:user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()

    context = {
        'form': form,
        'title': 'Create User',
        'action': 'Create',
    }
    return render(request, 'accounts/user_form.html', context)


@admin_required
def user_edit(request, pk):
    """
    Edit an existing user's details and role.
    Accessible to Administrators only.
    """
    user_obj = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'User "{user_obj.username}" has been updated successfully.',
            )
            return redirect('accounts:user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserEditForm(instance=user_obj)

    context = {
        'form': form,
        'user_obj': user_obj,
        'title': f'Edit User – {user_obj.username}',
        'action': 'Save Changes',
    }
    return render(request, 'accounts/user_form.html', context)


# ---------------------------------------------------------------------------
# Profile views
# ---------------------------------------------------------------------------

@login_required
def user_detail(request, pk):
    """
    Display the public profile of any user.
    Any authenticated user can view another user's profile.
    """
    user_obj = get_object_or_404(User, pk=pk)
    context = {
        'user_obj': user_obj,
        'title': f'Profile – {user_obj.get_full_name() or user_obj.username}',
    }
    return render(request, 'accounts/user_detail.html', context)


@login_required
def profile_view(request):
    """
    Display (and optionally edit) the currently logged-in user's own profile.
    Uses UserEditForm restricted to non-sensitive fields so the user can
    update their own contact details but not change their own role.
    """
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        # Non-admins should not be able to change their own role or active status
        if not request.user.is_admin_role:
            form.fields.pop('role', None)
            form.fields.pop('is_active', None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserEditForm(instance=request.user)
        if not request.user.is_admin_role:
            form.fields.pop('role', None)
            form.fields.pop('is_active', None)

    context = {
        'form': form,
        'title': 'My Profile',
    }
    return render(request, 'accounts/profile.html', context)
