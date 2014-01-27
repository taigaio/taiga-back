from django.contrib import admin

from .models import Domain, DomainMember

class DomainMemberInline(admin.TabularInline):
    model = DomainMember

class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')
    inlines = [ DomainMemberInline, ]

admin.site.register(Domain, DomainAdmin)
