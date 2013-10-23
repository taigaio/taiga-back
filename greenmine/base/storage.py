# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.files import storage

import django_sites as sites

class FileSystemStorage(storage.FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.MEDIA_URL.startswith("/"):
            site = sites.get_current()
            url_tmpl = "{scheme}//{domain}{url}"
            scheme = site.scheme and "{0}:".format(site.scheme) or ""
            self.base_url = url_tmpl.format(scheme=scheme, domain=site.domain,
                                            url=settings.MEDIA_URL)
