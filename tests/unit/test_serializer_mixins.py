# -*- coding: utf-8 -*-
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
