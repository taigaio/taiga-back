import pytest

from .. import factories as f
from django.db import models
from taiga.projects.mixins.serializers import ValidateDuplicatedNameInProjectMixin
from taiga.projects.models import Project

pytestmark = pytest.mark.django_db(transaction=True)

import factory


class TestingProjectModel(models.Model):
    pass

class TestingModelWithNameAttribute(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    project = models.ForeignKey(TestingProjectModel, null=False, blank=False)


class TestingSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = TestingModelWithNameAttribute


def test_duplicated_name_validation():
    project = TestingProjectModel.objects.create()
    instance_1 = TestingModelWithNameAttribute.objects.create(name="1", project=project)
    instance_2 = TestingModelWithNameAttribute.objects.create(name="2", project=project)

    # No duplicated_name
    serializer = TestingSerializer(data={"name": "3", "project": project.id})

    assert serializer.is_valid()

    # Create duplicated_name
    serializer = TestingSerializer(data={"name": "1", "project": project.id})

    assert not serializer.is_valid()

    # Update name to existing one
    serializer = TestingSerializer(data={"id": instance_2.id, "name": "1","project": project.id})

    assert not serializer.is_valid()
