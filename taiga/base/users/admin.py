# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User
from .forms import UserChangeForm, UserCreationForm


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
        return super().formfield_for_manytomany(
            db_field, request=request, **kwargs)


admin.site.register(Role, RoleAdmin)


class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'description', 'photo')}),
        (_('Extra info'), {'fields': ('color', 'default_language', 'default_timezone', 'token', 'colorize_tags')}),
        (_('Notifications info'), {'fields': ("notify_level", "notify_changes_by_me",)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    form = UserChangeForm
    add_form = UserCreationForm


class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'codename']
    list_filter = ['content_type']


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


admin.site.register(User, UserAdmin)
admin.site.register(Permission, PermissionAdmin)
