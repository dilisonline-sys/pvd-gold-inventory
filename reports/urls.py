from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('production/', views.production_report, name='production_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('orders/', views.order_report, name='order_report'),
    path('gold-consumption/', views.gold_consumption_report, name='gold_consumption_report'),
    path('worker-productivity/', views.worker_productivity, name='worker_productivity'),
]
