# -*- coding: utf-8 -*-
from django.utils.encoding import force_text

from taiga.base.api.utils import encoders

import json


def dumps(data, ensure_ascii=True, encoder_class=encoders.JSONEncoder, indent=None):
    return json.dumps(data, cls=encoder_class, ensure_ascii=ensure_ascii, indent=indent)


def loads(data):
    if isinstance(data, bytes):
        data = force_text(data)
    return json.loads(data)

load = json.load

# Some backward compatibility that should
# be removed in near future.
to_json = dumps
from_json = loads
