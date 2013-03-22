# -*- coding: utf-8 -*-
from django.contrib import admin

from guardian.admin import GuardedModelAdmin
import reversion

from greenmine.scrum.models import Project, Milestone, UserStory, Change, \
    ChangeAttachment, Task


class MilestoneInline(admin.TabularInline):
    model = Milestone
    fields = ('name', 'owner', 'estimated_start', 'estimated_finish', 'closed', 'disponibility', 'order')
    sortable_field_name = 'order'
    extra = 0

class UserStoryInline(admin.TabularInline):
    model = UserStory
    fields = ('subject', 'order')
    sortable_field_name = 'order'
    extra = 0

    def get_inline_instances(self, request, obj=None):
        if obj:
            return obj.user_stories.filter(mileston__isnone=True)
        else:
            return UserStory.objects.none()

class ProjectAdmin(reversion.VersionAdmin):
    list_display = ["name", "owner"]
    inlines = [MilestoneInline, UserStoryInline]

admin.site.register(Project, ProjectAdmin)


class MilestoneAdmin(reversion.VersionAdmin):
    list_display = ["name", "project", "owner", "closed", "estimated_start", "estimated_finish"]

admin.site.register(Milestone, MilestoneAdmin)


class UserStoryAdmin(reversion.VersionAdmin):
    list_display = ["ref", "milestone", "project", "owner"]

admin.site.register(UserStory, UserStoryAdmin)


class ChangeAdmin(reversion.VersionAdmin):
    list_display = ["id", "change_type", "project", "owner"]

admin.site.register(Change, ChangeAdmin)


class ChangeAttachmentAdmin(reversion.VersionAdmin):
    list_display = ["id", "change", "owner"]

admin.site.register(ChangeAttachment, ChangeAttachmentAdmin)


class TaskAdmin(reversion.VersionAdmin):
    list_display = ["subject", "type", "user_story"]

admin.site.register(Task, TaskAdmin)
