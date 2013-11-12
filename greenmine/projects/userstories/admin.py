# -*- coding: utf-8 -*-

from django.contrib import admin
import reversion

from greenmine.projects.admin import AttachmentInline

from . import models



class RolePointsInline(admin.TabularInline):
    model = models.RolePoints
    sortable_field_name = 'role'
    readonly_fields = ["user_story", "role", "points"]
    can_delete = False
    extra = 0
    max_num = 0


class RolePointsAdmin(admin.ModelAdmin):
    list_display = ["user_story", "role", "points"]
    list_display_links = list_display
    list_filter = ["role", "user_story__project"]
    readonly_fields = ["user_story", "role", "points"]


class UserStoryAdmin(reversion.VersionAdmin):
    list_display = ["project", "milestone",  "ref", "subject",]
    list_display_links = ["ref", "subject",]
    list_filter = ["project"]
    inlines = [RolePointsInline, AttachmentInline]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["status", "milestone"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                                      project=self.obj.project)
        elif (db_field.name in ["owner", "assigned_to"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name in ["watchers"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(models.UserStory, UserStoryAdmin)
admin.site.register(models.RolePoints, RolePointsAdmin)
