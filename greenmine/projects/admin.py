# -*- coding: utf-8 -*-

from django.contrib import admin
import reversion

from greenmine.projects.milestones.admin import MilestoneInline
from . import models



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
    # FIXME: commented because on save it raise strange
    # error 500 (seems bug in django)
    # inlines = [MembershipInline, MilestoneInline]

admin.site.register(models.Project, ProjectAdmin)
