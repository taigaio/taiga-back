# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
