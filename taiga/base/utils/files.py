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

import hashlib

from os import path, urandom
from unidecode import unidecode

from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.encoding import force_bytes

from taiga.base.utils.iterators import split_by_n

def get_file_path(instance, filename, base_path):
    basename = path.basename(filename).lower()
    base, ext = path.splitext(basename)
    base = slugify(unidecode(base))[0:100]
    basename = "".join([base, ext])

    hs = hashlib.sha256()
    hs.update(force_bytes(timezone.now().isoformat()))
    hs.update(urandom(1024))

    p1, p2, p3, p4, *p5 = split_by_n(hs.hexdigest(), 1)
    hash_part = path.join(p1, p2, p3, p4, "".join(p5))

    return path.join(base_path, hash_part, basename)
