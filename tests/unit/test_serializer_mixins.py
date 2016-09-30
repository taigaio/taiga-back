# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

import pytest

from django.db import models
from taiga.base.api.validators import ModelValidator
from taiga.projects.validators import DuplicatedNameInProjectValidator

pytestmark = pytest.mark.django_db(transaction=True)


class AuxProjectModel(models.Model):
    pass


class AuxModelWithNameAttribute(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    project = models.ForeignKey(AuxProjectModel, null=False, blank=False)


class AuxValidator(DuplicatedNameInProjectValidator, ModelValidator):
    class Meta:
        model = AuxModelWithNameAttribute


def test_duplicated_name_validation():
    project = AuxProjectModel.objects.create()
    AuxModelWithNameAttribute.objects.create(name="1", project=project)
    instance_2 = AuxModelWithNameAttribute.objects.create(name="2", project=project)

    # No duplicated_name
    validator = AuxValidator(data={"name": "3", "project": project.id})

    assert validator.is_valid()

    # Create duplicated_name
    validator = AuxValidator(data={"name": "1", "project": project.id})

    assert not validator.is_valid()

    # Update name to existing one
    validator = AuxValidator(data={"id": instance_2.id, "name": "1", "project": project.id})

    assert not validator.is_valid()
