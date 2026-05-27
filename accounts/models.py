from django.contrib.auth.models import AbstractUser
from django.db import models


ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_SUPERVISOR = 'supervisor'
ROLE_PRODUCTION_WORKER = 'production_worker'
ROLE_INVENTORY_CLERK = 'inventory_clerk'
ROLE_VIEWER = 'viewer'

ROLES = [
    (ROLE_ADMIN, 'Administrator'),
    (ROLE_MANAGER, 'Manager'),
    (ROLE_SUPERVISOR, 'Supervisor'),
    (ROLE_PRODUCTION_WORKER, 'Production Worker'),
    (ROLE_INVENTORY_CLERK, 'Inventory Clerk'),
    (ROLE_VIEWER, 'Viewer'),
]


class User(AbstractUser):
    """
    Custom user model for the PVD Gold Inventory / Goldsmith Manufacturing system.

    Extends Django's AbstractUser so we keep all built-in auth behaviour
    (password hashing, session framework, admin integration) while adding
    goldsmith-specific fields.

    AbstractUser already provides: username, email, first_name, last_name,
    is_active, is_staff, is_superuser, date_joined, last_login, password.
    """

    role = models.CharField(
        max_length=30,
        choices=ROLES,
        default=ROLE_VIEWER,
        verbose_name='Role',
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Employee ID',
        help_text='Unique identifier assigned by HR.',
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Phone Number',
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Department',
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        full = self.get_full_name()
        return full if full.strip() else self.username

    # ------------------------------------------------------------------
    # Convenience role-check helpers
    # ------------------------------------------------------------------

    @property
    def is_admin_role(self):
        return self.role == ROLE_ADMIN

    @property
    def is_manager_role(self):
        return self.role == ROLE_MANAGER

    @property
    def is_supervisor_role(self):
        return self.role == ROLE_SUPERVISOR

    @property
    def is_production_worker_role(self):
        return self.role == ROLE_PRODUCTION_WORKER

    @property
    def is_inventory_clerk_role(self):
        return self.role == ROLE_INVENTORY_CLERK

    @property
    def is_viewer_role(self):
        return self.role == ROLE_VIEWER

    @property
    def is_manager_or_above(self):
        return self.role in (ROLE_ADMIN, ROLE_MANAGER)

    @property
    def is_supervisor_or_above(self):
        return self.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR)
