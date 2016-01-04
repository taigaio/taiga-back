# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from django.template.defaultfilters import slugify as django_slugify

import time

from unidecode import unidecode


def slugify(value):
    """
    Return a slug
    """
    return django_slugify(unidecode(value or ""))


def slugify_uniquely(value, model, slugfield="slug"):
    """
    Returns a slug on a name which is unique within a model's table
    """

    suffix = 0
    potential = base = django_slugify(unidecode(value))
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not model.objects.filter(**{slugfield: potential}).exists():
            return potential
        suffix += 1


def slugify_uniquely_for_queryset(value, queryset, slugfield="slug"):
    """
    Returns a slug on a name which doesn't exist in a queryset
    """

    suffix = 0
    potential = base = django_slugify(unidecode(value))
    if len(potential) == 0:
        potential = 'null'
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not queryset.filter(**{slugfield: potential}).exists():
            return potential
        suffix += 1


def ref_uniquely(p, seq_field,  model, field='ref'):
    project = p.__class__.objects.select_for_update().get(pk=p.pk)
    ref = getattr(project, seq_field) + 1

    while True:
        params = {field: ref, 'project': project}
        if not model.objects.filter(**params).exists():
            setattr(project, seq_field, ref)
            project.save(update_fields=[seq_field])
            return ref

        time.sleep(0.0002)
        ref += 1
