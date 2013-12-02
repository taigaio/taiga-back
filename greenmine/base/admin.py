from django.contrib import admin
from .models import Site


class SiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')

admin.site.register(Site, SiteAdmin)
