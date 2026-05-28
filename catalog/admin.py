from django.contrib import admin
from .models import CatalogSettings


@admin.register(CatalogSettings)
class CatalogSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'updated_at')
    readonly_fields = ('updated_at',)

    def save_model(self, request, obj, form, change):
        raw = request.POST.get('raw_password', '').strip()
        if raw:
            obj.set_password(raw)
        super().save_model(request, obj, form, change)
