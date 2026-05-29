from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    # Job Orders
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('<int:pk>/status/', views.update_order_status, name='update_order_status'),
    path('<int:pk>/delivery/', views.order_delivery, name='order_delivery'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
]
