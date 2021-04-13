# -*- coding: utf-8 -*-
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
