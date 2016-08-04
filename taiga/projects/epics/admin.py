# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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


class RelatedUserStoriesInline(admin.TabularInline):
    model = models.RelatedUserStory
    sortable_field_name = "order"
    raw_id_fields = ["user_story", ]
    extra = 0


class EpicAdmin(admin.ModelAdmin):
    list_display = ["project", "ref", "subject"]
    list_display_links = ["ref", "subject"]
    inlines = [WatchedInline, VoteInline, RelatedUserStoriesInline]
    raw_id_fields = ["project"]
    search_fields = ["subject", "description", "id", "ref"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["status"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.model.objects.filter(project=self.obj.project)

        elif (db_field.name in ["owner", "assigned_to"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.model.objects.filter(memberships__project=self.obj.project)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name in ["watchers"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(memberships__project=self.obj.project)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(models.Epic, EpicAdmin)
