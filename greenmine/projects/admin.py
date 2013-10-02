# -*- coding: utf-8 -*-

from django.contrib import admin

from greenmine.projects.milestones.admin import MilestoneInline
from greenmine.projects.userstories.admin import UserStoryInline

from . import models

import reversion


class AttachmentAdmin(reversion.VersionAdmin):
    list_display = ["id", "owner"]

admin.site.register(models.Attachment, AttachmentAdmin)


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'role', 'user']
    list_filter = ['project', 'role']

admin.site.register(models.Membership, MembershipAdmin)


class MembershipInline(admin.TabularInline):
    model = models.Membership
    fields = ('user', 'project', 'role')
    extra = 0


class ProjectAdmin(reversion.VersionAdmin):
    list_display = ["name", "owner"]
    inlines = [MembershipInline, MilestoneInline, UserStoryInline]

admin.site.register(models.Project, ProjectAdmin)
