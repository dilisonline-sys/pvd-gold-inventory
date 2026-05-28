from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_gallery, name='gallery'),
    path('login/', views.catalog_login, name='login'),
    path('logout/', views.catalog_logout, name='logout'),
    path('product/<int:pk>/', views.catalog_product, name='product'),
]
