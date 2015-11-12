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

from . import models


class BaseCustomAttributeAdmin:
    list_display = ["id", "name", "type", "project", "order"]
    list_display_links = ["id", "name"]
    fieldsets = (
        (None, {
            "fields": ("name", "type", "description", ("project", "order"))
        }),
        ("Advanced options", {
            "classes": ("collapse",),
            "fields": (("created_date", "modified_date"),)
        })
    )
    readonly_fields = ("created_date", "modified_date")
    search_fields = ["id", "name", "project__name", "project__slug"]
    raw_id_fields = ["project"]


@admin.register(models.UserStoryCustomAttribute)
class UserStoryCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass


@admin.register(models.TaskCustomAttribute)
class TaskCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass


@admin.register(models.IssueCustomAttribute)
class IssueCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass
