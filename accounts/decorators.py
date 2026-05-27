from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_SUPERVISOR,
    ROLE_PRODUCTION_WORKER,
    ROLE_INVENTORY_CLERK,
    ROLE_VIEWER,
)


def role_required(*roles):
    """
    Decorator factory that restricts a view to users whose ``role`` field
    is among the given role strings.

    - Unauthenticated users are redirected to the login page (preserving
      the ``next`` query parameter so they return after login).
    - Authenticated users whose role is not in *roles* receive a plain
      HTTP 403 Forbidden response.

    Usage::

        @role_required('admin', 'manager')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = '/accounts/login/'
                next_url = request.get_full_path()
                return redirect(f'{login_url}?{REDIRECT_FIELD_NAME}={next_url}')

            if request.user.role not in roles:
                return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1>'
                    '<p>You do not have permission to access this page.</p>'
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ------------------------------------------------------------------
# Convenience shortcuts
# ------------------------------------------------------------------

def admin_required(view_func):
    """Allow access to Administrators only."""
    return role_required(ROLE_ADMIN)(view_func)


def manager_or_above(view_func):
    """Allow access to Administrators and Managers."""
    return role_required(ROLE_ADMIN, ROLE_MANAGER)(view_func)


def supervisor_or_above(view_func):
    """Allow access to Administrators, Managers, and Supervisors."""
    return role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR)(view_func)
