# -*- coding: utf-8 -*-
from django.contrib import admin

from guardian.admin import GuardedModelAdmin
import reversion

from greenmine.scrum.models import Project, Milestone, UserStory, Change, \
    ChangeAttachment, Task


class ProjectAdmin(GuardedModelAdmin, reversion.VersionAdmin):
    list_display = ["name", "owner"]

admin.site.register(Project, ProjectAdmin)


class MilestoneAdmin(reversion.VersionAdmin):
    list_display = ["name", "project", "owner"]

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
