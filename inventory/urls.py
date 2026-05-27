from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Materials
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),

    # Stock entries
    path('stock/entry/', views.stock_entry, name='stock_entry'),
    path('stock/bulk-entry/', views.bulk_stock_entry, name='bulk_stock_entry'),

    # Stock history & adjustments
    path('stock/history/', views.stock_history, name='stock_history'),
    path('stock/adjustment/', views.stock_adjustment, name='stock_adjustment'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),

    # Alerts
    path('alerts/low-stock/', views.low_stock_alerts, name='low_stock_alerts'),
]
