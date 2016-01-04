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

from taiga.base.utils.urls import get_absolute_url

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError


def _get_attachment_thumbnailer_url(attachment, thumbnailer_size):
    try:
        thumb_url = get_thumbnailer(attachment.attached_file)[thumbnailer_size].url
        thumb_url = get_absolute_url(thumb_url)
    except InvalidImageFormatError:
        thumb_url = None

    return thumb_url


def get_timeline_image_thumbnailer_url(attachment):
    return _get_attachment_thumbnailer_url(attachment, "timeline-image")


def get_card_image_thumbnailer_url(attachment):
    return _get_attachment_thumbnailer_url(attachment, "card-image")
