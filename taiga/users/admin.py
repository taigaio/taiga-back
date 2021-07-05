# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

from django.apps import apps

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from django.utils.translation import ugettext_lazy as _

from .models import Role, User
from .forms import UserChangeForm, UserCreationForm


admin.site.unregister(Group)


## Inlines

class MembershipsInline(admin.TabularInline):
    model = apps.get_model("projects", "Membership")
    fk_name = "user"
    verbose_name = _("Project Member")
    verbose_name_plural = _("Project Members")
    fields = ("project_id", "project_name", "project_slug", "project_is_private",
              "project_owner", "is_admin")
    readonly_fields = ("project_id", "project_name", "project_slug", "project_is_private",
                       "project_owner", "is_admin")
    show_change_link = True
    extra = 0

    def project_id(self, obj):
        return obj.project.id if obj.project else None
    project_id.short_description = _("id")

    def project_name(self, obj):
        return obj.project.name if obj.project else None
    project_name.short_description = _("name")

    def project_slug(self, obj):
        return obj.project.slug if obj.project else None
    project_slug.short_description = _("slug")

    def project_is_private(self, obj):
        return obj.project.is_private if obj.project else None
    project_is_private.short_description = _("is private")
    project_is_private.boolean = True

    def project_owner(self, obj):
        if obj.project and obj.project.owner:
            return "{} (@{})".format(obj.project.owner.get_full_name(), obj.project.owner.username)
        return None
    project_owner.short_description = _("owner")

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False


class OwnedProjectsInline(admin.TabularInline):
    model = apps.get_model("projects", "Project")
    fk_name = "owner"
    verbose_name = _("Project Ownership")
    verbose_name_plural = _("Project Ownerships")
    fields = ("id", "name", "slug", "is_private")
    readonly_fields = ("id", "name", "slug", "is_private")
    show_change_link = True
    extra = 0

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


## Admin panels

class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            qs = kwargs.get("queryset", db_field.rel.to.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs["queryset"] = qs.select_related("content_type")
        return super().formfield_for_manytomany(
            db_field, request=request, **kwargs)


class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("full_name", "email", "bio", "photo")}),
        (_("Extra info"), {"fields": ("color", "lang", "timezone", "token", "colorize_tags",
                                      "email_token", "new_email", "verified_email", "accepted_terms", "read_new_terms")}),
        (_("Permissions"), {"fields": ("is_active", "is_superuser")}),
        (_("Restrictions"), {"fields": (("max_private_projects", "max_memberships_private_projects"),
                                        ("max_public_projects", "max_memberships_public_projects"))}),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "date_cancelled")}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')}
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("username", "email", "full_name")
    list_filter = ("is_superuser", "is_active", "verified_email")
    search_fields = ("username", "full_name", "email")
    ordering = ("username",)
    filter_horizontal = ()
    inlines = [
        OwnedProjectsInline,
        MembershipsInline
    ]


admin.site.register(User, UserAdmin)
