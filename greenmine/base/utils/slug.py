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



def ref_uniquely(p, seq_field,  model, field='ref'):
    """
    Returns a unique reference code based on base64 and time.
    """
    project = project.__class__.objects.select_for_update().get(pk=p.pk)

    ref = getattr(project, seq_field) + 1

    while True:
        params = {field: ref, 'project': _project}
        if not model.objects.filter(**params).exists():
            setattr(_project, seq_field, ref)
            _project.save(update_fields=[seq_field])
            return ref

        time.sleep(0.0002)
        ref += 1
