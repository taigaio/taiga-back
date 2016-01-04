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

from taiga.projects.attachments.admin import AttachmentInline
from taiga.projects.notifications.admin import WatchedInline
from taiga.projects.votes.admin import VoteInline

from taiga.projects.wiki.models import WikiPage

from . import models

class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["project", "slug", "owner"]
    list_display_links = list_display
    inlines = [WatchedInline, VoteInline]
    raw_id_fields = ["project"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["owner", "last_modifier"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(models.WikiPage, WikiPageAdmin)

class WikiLinkAdmin(admin.ModelAdmin):
    list_display = ["project", "title"]
    list_display_links = list_display
    raw_id_fields = ["project"]

admin.site.register(models.WikiLink, WikiLinkAdmin)
