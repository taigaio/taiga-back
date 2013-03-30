from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

from greenmine.base.models import Role, User

admin.site.unregister(Group)

class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ('permissions',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.rel.to.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs['queryset'] = qs.select_related('content_type')
        return super(RoleAdmin, self).formfield_for_manytomany(
            db_field, request=request, **kwargs)

admin.site.register(Role, RoleAdmin)
admin.site.register(User, UserAdmin)
