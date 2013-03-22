# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.profile.models import Profile, Role


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user"]

admin.site.register(Profile, ProfileAdmin)


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
