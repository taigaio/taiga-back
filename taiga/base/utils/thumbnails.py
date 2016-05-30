# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
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

import os

from django.db.models.fields.files import FieldFile

from taiga.base.utils.urls import get_absolute_url

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError


def get_thumbnail_url(file_obj, thumbnailer_size):
    # Ugly hack to temporary ignore tiff files
    relative_name = file_obj
    if isinstance(file_obj, FieldFile):
        relative_name = file_obj.name

    source_extension = os.path.splitext(relative_name)[1][1:]
    if source_extension == "tiff":
        return None

    try:
        path_url = get_thumbnailer(file_obj)[thumbnailer_size].url
        thumb_url = get_absolute_url(path_url)
    except InvalidImageFormatError:
        thumb_url = None

    return thumb_url
