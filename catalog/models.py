from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.db import models


class CatalogSettings(models.Model):
    """Singleton that holds the shared password for the public product catalog."""

    _password = models.CharField(max_length=256, verbose_name='Access Password (hashed)',
                                 db_column='password')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catalog Settings'
        verbose_name_plural = 'Catalog Settings'

    def __str__(self):
        return 'Catalog Settings'

    def set_password(self, raw):
        self._password = make_password(raw)

    def check_password(self, raw):
        return django_check_password(raw, self._password)

    @classmethod
    def get(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        if created:
            obj.set_password('catalog123')
            obj.save()
        return obj
