# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from .cleanup_files import cleanup_post_delete
from easy_thumbnails.files import get_thumbnailer


def _delete_thumbnail_files(**kwargs):
    thumbnailer = get_thumbnailer(kwargs["file"])
    thumbnailer.delete_thumbnails()


def connect_thumbnail_signals():
    cleanup_post_delete.connect(_delete_thumbnail_files)


def disconnect_thumbnail_signals():
    cleanup_post_delete.disconnect(_delete_thumbnail_files)
