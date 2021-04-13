# -*- coding: utf-8 -*-
import pytest

from django.db import models
from taiga.base.api.validators import ModelValidator
from taiga.projects.validators import DuplicatedNameInProjectValidator

pytestmark = pytest.mark.django_db(transaction=True)


class AuxProjectModel(models.Model):
    pass


class AuxModelWithNameAttribute(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    project = models.ForeignKey(AuxProjectModel, null=False, blank=False, on_delete=models.CASCADE)


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
