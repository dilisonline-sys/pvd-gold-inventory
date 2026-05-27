"""
Top-level dashboard URL entry-point.
Mounted at /dashboard/ in the root URL config.
"""
from django.urls import path
from . import dashboard_view

urlpatterns = [
    path('', dashboard_view.main_dashboard, name='dashboard'),
]
