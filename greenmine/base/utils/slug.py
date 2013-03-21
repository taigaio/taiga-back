# -*- coding: utf-8 -*-

from django.utils import baseconv
from django.template.defaultfilters import slugify

import time


def slugify_uniquely(value, model, slugfield="slug"):
    """
    Returns a slug on a name which is unique within a model's table
    """

    suffix = 0
    potential = base = slugify(value)
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not model.objects.filter(**{slugfield: potential}).count():
            return potential
        suffix += 1


def ref_uniquely(project, model, field='ref'):
    """
    Returns a unique reference code based on base64 and time.
    """

    # this prevents concurrent and inconsistent references.
    time.sleep(0.001)

    new_timestamp = lambda: int("".join(str(time.time()).split(".")))
    while True:
        potential = baseconv.base62.encode(new_timestamp())
        params = {field: potential, 'project': project}
        if not model.objects.filter(**params).exists():
            return potential

        time.sleep(0.0002)
