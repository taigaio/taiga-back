# Copyright (C) 2014-2016 Taiga Agile LLC <taiga@taiga.io>
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

from django.conf import settings

from taiga.base.utils.thumbnails import get_thumbnail_url


def get_timeline_image_thumbnail_url(attachment):
    if attachment.attached_file:
        return get_thumbnail_url(attachment.attached_file, settings.THN_ATTACHMENT_TIMELINE)
    return None


def get_card_image_thumbnail_url(attachment):
    if attachment.attached_file:
        return get_thumbnail_url(attachment.attached_file, settings.THN_ATTACHMENT_CARD)
    return None
