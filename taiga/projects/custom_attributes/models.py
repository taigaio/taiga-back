# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from taiga.base.db.models.fields import JSONField

from taiga.base.utils.time import timestamp_ms
from taiga.projects.occ.mixins import OCCModelMixin

from . import choices


######################################################
#  Custom Attribute Models
#######################################################

class AbstractCustomAttribute(models.Model):
    name = models.CharField(null=False, blank=False, max_length=64, verbose_name=_("name"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    type = models.CharField(null=False, blank=False, max_length=16,
                            choices=choices.TYPES_CHOICES, default=choices.TEXT_TYPE,
                            verbose_name=_("type"))
    order = models.BigIntegerField(null=False, blank=False, default=timestamp_ms, verbose_name=_("order"))
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="%(class)ss",
        verbose_name=_("project"),
        on_delete=models.CASCADE,
    )
    extra = JSONField(blank=True, default=None, null=True)
    created_date = models.DateTimeField(null=False, blank=False, default=timezone.now,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    _importing = None

    class Meta:
        abstract = True
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_date = timezone.now()

        return super().save(*args, **kwargs)


class EpicCustomAttribute(AbstractCustomAttribute):
    class Meta(AbstractCustomAttribute.Meta):
        verbose_name = "epic custom attribute"
        verbose_name_plural = "epic custom attributes"


class UserStoryCustomAttribute(AbstractCustomAttribute):
    class Meta(AbstractCustomAttribute.Meta):
        verbose_name = "user story custom attribute"
        verbose_name_plural = "user story custom attributes"


class TaskCustomAttribute(AbstractCustomAttribute):
    class Meta(AbstractCustomAttribute.Meta):
        verbose_name = "task custom attribute"
        verbose_name_plural = "task custom attributes"


class IssueCustomAttribute(AbstractCustomAttribute):
    class Meta(AbstractCustomAttribute.Meta):
        verbose_name = "issue custom attribute"
        verbose_name_plural = "issue custom attributes"


######################################################
#  Custom Attributes Values Models
#######################################################

class AbstractCustomAttributesValues(OCCModelMixin, models.Model):
    attributes_values = JSONField(null=False, blank=False, default=dict, verbose_name=_("values"))

    class Meta:
        abstract = True
        ordering = ["id"]


class EpicCustomAttributesValues(AbstractCustomAttributesValues):
    epic = models.OneToOneField(
        "epics.Epic",
        null=False,
        blank=False,
        related_name="custom_attributes_values",
        verbose_name=_("epic"),
        on_delete=models.CASCADE,
    )

    class Meta(AbstractCustomAttributesValues.Meta):
        verbose_name = "epic custom attributes values"
        verbose_name_plural = "epic custom attributes values"
        index_together = [("epic",)]

    @property
    def project(self):
        # NOTE: This property simplifies checking permissions
        return self.epic.project


class UserStoryCustomAttributesValues(AbstractCustomAttributesValues):
    user_story = models.OneToOneField(
        "userstories.UserStory",
        null=False,
        blank=False,
        related_name="custom_attributes_values",
        verbose_name=_("user story"),
        on_delete=models.CASCADE,
    )

    class Meta(AbstractCustomAttributesValues.Meta):
        verbose_name = "user story custom attributes values"
        verbose_name_plural = "user story custom attributes values"
        index_together = [("user_story",)]

    @property
    def project(self):
        # NOTE: This property simplifies checking permissions
        return self.user_story.project


class TaskCustomAttributesValues(AbstractCustomAttributesValues):
    task = models.OneToOneField(
        "tasks.Task",
        null=False,
        blank=False,
        related_name="custom_attributes_values",
        verbose_name=_("task"),
        on_delete=models.CASCADE,
    )

    class Meta(AbstractCustomAttributesValues.Meta):
        verbose_name = "task custom attributes values"
        verbose_name_plural = "task custom attributes values"
        index_together = [("task",)]

    @property
    def project(self):
        # NOTE: This property simplifies checking permissions
        return self.task.project


class IssueCustomAttributesValues(AbstractCustomAttributesValues):
    issue = models.OneToOneField(
        "issues.Issue",
        null=False,
        blank=False,
        related_name="custom_attributes_values",
        verbose_name=_("issue"),
        on_delete=models.CASCADE,
    )

    class Meta(AbstractCustomAttributesValues.Meta):
        verbose_name = "issue custom attributes values"
        verbose_name_plural = "issue custom attributes values"
        index_together = [("issue",)]

    @property
    def project(self):
        # NOTE: This property simplifies checking permissions
        return self.issue.project
