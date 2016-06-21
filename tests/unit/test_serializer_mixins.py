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

from .. import factories as f
from django.db import models
from taiga.projects.mixins.serializers import ValidateDuplicatedNameInProjectMixin
from taiga.projects.models import Project

pytestmark = pytest.mark.django_db(transaction=True)

import factory


class AuxProjectModel(models.Model):
    pass

class AuxModelWithNameAttribute(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    project = models.ForeignKey(AuxProjectModel, null=False, blank=False)


class AuxSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = AuxModelWithNameAttribute



def test_duplicated_name_validation():
    project = AuxProjectModel.objects.create()
    instance_1 = AuxModelWithNameAttribute.objects.create(name="1", project=project)
    instance_2 = AuxModelWithNameAttribute.objects.create(name="2", project=project)

    # No duplicated_name
    serializer = AuxSerializer(data={"name": "3", "project": project.id})

    assert serializer.is_valid()

    # Create duplicated_name
    serializer = AuxSerializer(data={"name": "1", "project": project.id})

    assert not serializer.is_valid()

    # Update name to existing one
    serializer = AuxSerializer(data={"id": instance_2.id, "name": "1","project": project.id})

    assert not serializer.is_valid()
