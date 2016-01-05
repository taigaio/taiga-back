# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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


class FeedbackEntryAdmin(admin.ModelAdmin):
    list_display = ['created_date', 'full_name', 'email' ]
    list_display_links = list_display
    list_filter = ['created_date',]
    date_hierarchy = "created_date"
    ordering = ("-created_date", "id")
    search_fields = ("full_name", "email", "id")


admin.site.register(models.FeedbackEntry, FeedbackEntryAdmin)
