# -*- coding: utf-8 -*-
from .cleanup_files import cleanup_post_delete
from easy_thumbnails.files import get_thumbnailer


def _delete_thumbnail_files(**kwargs):
    thumbnailer = get_thumbnailer(kwargs["file"])
    thumbnailer.delete_thumbnails()


def connect_thumbnail_signals():
    cleanup_post_delete.connect(_delete_thumbnail_files)


def disconnect_thumbnail_signals():
    cleanup_post_delete.disconnect(_delete_thumbnail_files)
