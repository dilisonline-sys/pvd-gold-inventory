from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("inventory/", include("inventory.urls", namespace="inventory")),
    path("manufacturing/", include("manufacturing.urls", namespace="manufacturing")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("reports/", include("reports.urls", namespace="reports")),
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
    path("dashboard/", include("manufacturing.dashboard_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
