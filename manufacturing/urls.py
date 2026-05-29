from django.urls import path

from . import views

app_name = 'manufacturing'

urlpatterns = [
    # Dashboards
    path('', views.production_dashboard, name='production_dashboard'),
    path('stage-dashboard/', views.stage_dashboard, name='stage_dashboard'),
    path('stage-dashboard/<int:stage_pk>/', views.stage_dashboard, name='stage_dashboard_filtered'),

    # Production Jobs
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),

    # Stage actions (POST-only for update/advance)
    path('jobs/<int:pk>/update-stage/', views.update_stage, name='update_stage'),

    # Materials
    path('jobs/<int:pk>/issue-materials/', views.issue_materials, name='issue_materials'),
    path('jobs/<int:pk>/requirements/add/', views.requirement_add, name='requirement_add'),
    path('jobs/<int:pk>/requirements/auto-calculate/', views.requirement_auto_calculate, name='requirement_auto_calculate'),
    path('requirements/<int:req_pk>/delete/', views.requirement_delete, name='requirement_delete'),

    # Quality checks
    path('process-records/<int:record_pk>/quality-check/', views.quality_check_create, name='quality_check_create'),

    # Final product (job-linked — from job detail page)
    path('jobs/<int:pk>/final-product/', views.final_product_create, name='final_product_create'),

    # Catalog (standalone entry, edit, bulk upload)
    path('final-products/', views.final_product_inventory, name='final_product_inventory'),
    path('final-products/add/', views.catalog_add, name='catalog_add'),
    path('final-products/<int:pk>/edit/', views.catalog_edit, name='catalog_edit'),
    path('final-products/bulk-upload/', views.catalog_bulk_upload, name='catalog_bulk_upload'),
]
