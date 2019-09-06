# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from psd_tools import PSDImage
from django.db.models.fields.files import FieldFile

from taiga.base.utils.urls import get_absolute_url

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError
from PIL import Image
from PIL.PngImagePlugin import PngImageFile

from io import BytesIO

# SVG thumbnail generator
try:
    from cairosvg.surface import PNGSurface
    from cairosvg.url import fetch
    import magic

    def url_fetcher(url, resource_type):
        if url.startswith("data:"):
            return fetch(url, resource_type)
        return b""


    def svg_image_factory(fp, filename):
        mime_type = magic.from_buffer(fp.read(1024), mime=True)
        if mime_type != "image/svg+xml":
            raise TypeError

        fp.seek(0)
        png_data = PNGSurface.convert(fp.read(), url_fetcher=url_fetcher)
        return PngImageFile(BytesIO(png_data))

    Image.register_mime("SVG", "image/svg+xml")
    Image.register_extension("SVG", ".svg")
    Image.register_open("SVG", svg_image_factory)
except Exception:
    pass

Image.init()


# PSD thumbnail generator
def psd_image_factory(data, *args):
    try:
        return PSDImage.open(data).compose()
    except Exception:
        raise TypeError


Image.register_open("PSD", psd_image_factory)


def get_thumbnail(file_obj, thumbnailer_size):
    # Ugly hack to temporary ignore tiff files
    relative_name = file_obj
    if isinstance(file_obj, FieldFile):
        relative_name = file_obj.name

    source_extension = os.path.splitext(relative_name)[1][1:]
    if source_extension not in ('png', 'svg', 'gif', 'bmp', 'jpeg', 'jpg'):
        return None

    try:
        thumbnailer = get_thumbnailer(file_obj)
        return thumbnailer[thumbnailer_size]
    except InvalidImageFormatError:
        return None


def get_thumbnail_url(file_obj, thumbnailer_size):
    thumbnail = get_thumbnail(file_obj, thumbnailer_size)

    if not thumbnail:
        return None

    path_url = thumbnail.url
    thumb_url = get_absolute_url(path_url)
    return thumb_url
