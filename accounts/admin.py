from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, ROLES


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.

    Extends Django's built-in UserAdmin so that all standard password-change
    functionality, permission management, and group assignments still work,
    while also surfacing the goldsmith-specific fields.
    """

    # Columns shown in the list view
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'employee_id',
        'department',
        'is_active',
        'is_staff',
        'date_joined',
    )

    # Filters in the right-hand sidebar
    list_filter = ('role', 'department', 'is_active', 'is_staff', 'is_superuser')

    # Fields that are searchable via the search bar
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')

    # Default ordering
    ordering = ('username',)

    # Allow clicking directly on ``username`` column to open the record
    list_display_links = ('username',)

    # Make ``role`` editable from the list view
    list_editable = ('is_active',)

    # ------------------------------------------------------------------
    # Detail / change-form layout
    # ------------------------------------------------------------------

    # Inject the custom fields into the existing BaseUserAdmin fieldsets.
    # We add a new "Goldsmith Profile" section beneath the standard ones.
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            'Goldsmith Profile',
            {
                'fields': ('role', 'employee_id', 'phone', 'department'),
                'classes': ('wide',),
            },
        ),
    )

    # Fields shown on the "Add user" form (before a user record exists)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            'Goldsmith Profile',
            {
                'fields': ('role', 'employee_id', 'phone', 'department'),
                'classes': ('wide',),
            },
        ),
    )

    # Read-only fields on the change form
    readonly_fields = ('date_joined', 'last_login')
