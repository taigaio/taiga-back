# -*- coding: utf-8 -*-

import json
from rest_framework.utils import encoders


def to_json(data, ensure_ascii=True, encoder_class=encoders.JSONEncoder):
    return json.dumps(data, cls=encoder_class, indent=None, ensure_ascii=ensure_ascii)


def from_json(data):
    return json.loads(data)
