from django.contrib import admin

from .models import Domain


class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')

admin.site.register(Domain, DomainAdmin)
