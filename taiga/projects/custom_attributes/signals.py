# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from . import models


def create_custom_attribute_value_when_create_epic(sender, instance, created, **kwargs):
    if created:
        models.EpicCustomAttributesValues.objects.get_or_create(epic=instance,
                                                                defaults={"attributes_values":{}})


def create_custom_attribute_value_when_create_user_story(sender, instance, created, **kwargs):
    if created:
        models.UserStoryCustomAttributesValues.objects.get_or_create(user_story=instance,
                                                             defaults={"attributes_values":{}})


def create_custom_attribute_value_when_create_task(sender, instance, created, **kwargs):
    if created:
        models.TaskCustomAttributesValues.objects.get_or_create(task=instance,
                                                        defaults={"attributes_values":{}})


def create_custom_attribute_value_when_create_issue(sender, instance, created, **kwargs):
    if created:
        models.IssueCustomAttributesValues.objects.get_or_create(issue=instance,
                                                         defaults={"attributes_values":{}})
