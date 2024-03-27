# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.encoding import force_str

from taiga.base.api.utils import encoders

import json


def dumps(data, ensure_ascii=True, encoder_class=encoders.JSONEncoder, indent=None):
    return json.dumps(data, cls=encoder_class, ensure_ascii=ensure_ascii, indent=indent)


def loads(data):
    if isinstance(data, bytes):
        data = force_str(data)
    return json.loads(data)

load = json.load

# Some backward compatibility that should
# be removed in near future.
to_json = dumps
from_json = loads
