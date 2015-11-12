# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.contrib import admin
from taiga.projects.notifications.admin import WatchedInline
from taiga.projects.votes.admin import VoteInline

from . import models


class MilestoneInline(admin.TabularInline):
    model = models.Milestone
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # Hack! Hook parent obj just in time to use in formfield_for_manytomany
        self.parent_obj = obj
        return super(MilestoneInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["owner"]):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                                         memberships__project=self.parent_obj)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "owner", "closed", "estimated_start",
                    "estimated_finish"]
    list_display_links = list_display
    readonly_fields = ["owner"]
    inlines = [WatchedInline, VoteInline]
    search_fields = ["name", "id"]
    raw_id_fields = ["project"]


admin.site.register(models.Milestone, MilestoneAdmin)
