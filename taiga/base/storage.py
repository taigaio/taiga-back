# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
