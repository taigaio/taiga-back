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

from easy_thumbnails.files import get_thumbnailer

from django.apps import AppConfig
from django.apps import apps
from django_transactional_cleanup.signals import cleanup_post_delete


def thumbnail_delete(**kwargs):
    thumbnailer = get_thumbnailer(kwargs["file"])
    thumbnailer.delete_thumbnails()


def connect_attachment_signals():
    cleanup_post_delete.connect(thumbnail_delete)


class AttachmentsAppConfig(AppConfig):
    name = "taiga.projects.attachments"
    verbose_name = "Attachments"

    def ready(self):
        connect_attachment_signals()
