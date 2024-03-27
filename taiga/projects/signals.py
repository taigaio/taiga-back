# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.conf import settings
from django.db.models import F
from django.dispatch import Signal

from taiga.projects.notifications.services import create_notify_policy_if_not_exists


####################################
# Signals over project items
####################################

## Membership

def membership_post_delete(sender, instance, using, **kwargs):
    instance.project.update_role_points()


def membership_post_save(sender, instance, using, **kwargs):
    if not instance.user:
        return
    create_notify_policy_if_not_exists(instance.project, instance.user)

    # Set project on top on user projects list
    membership = apps.get_model("projects", "Membership")
    membership.objects.filter(user=instance.user) \
        .update(user_order=F('user_order') + 1)

    membership.objects.filter(user=instance.user, project=instance.project)\
        .update(user_order=0)


## project attributes
def project_post_save(sender, instance, created, **kwargs):
    """
    Populate new project dependen default data
    """
    if not created:
        return

    if instance._importing:
        return

    template = getattr(instance, "creation_template", None)
    if template is None:
        ProjectTemplate = apps.get_model("projects", "ProjectTemplate")
        template = ProjectTemplate.objects.get(slug=settings.DEFAULT_PROJECT_TEMPLATE)

    if instance.tags:
        template.tags = instance.tags

    if instance.tags_colors:
        template.tags_colors = instance.tags_colors

    template.apply_to_project(instance)

    instance.save()

    Role = apps.get_model("users", "Role")
    try:
        owner_role = instance.roles.get(slug=template.default_owner_role)
    except Role.DoesNotExist:
        owner_role = instance.roles.first()

    if owner_role:
        Membership = apps.get_model("projects", "Membership")
        Membership.objects.create(user=instance.owner, project=instance, role=owner_role,
                                  is_admin=True, email=instance.owner.email)


## swimlanes
def create_swimlane_user_story_statuses_on_swimalne_post_save(sender, instance, created, **kwargs):
    """
    Populate new swimlanes with SwimlaneUserStoryStatus objects.
    """
    if not created:
        return

    if instance._importing:
        return

    SwimlaneUserStoryStatus = apps.get_model("projects", "SwimlaneUserStoryStatus")
    copy_from_main_status = instance.project.swimlanes.count() == 1
    objects = (
        SwimlaneUserStoryStatus(
            swimlane=instance,
            status=status,
            wip_limit=status.wip_limit if copy_from_main_status else None
        )
    for status in instance.project.us_statuses.all())

    SwimlaneUserStoryStatus.objects.bulk_create(objects)


def set_default_project_swimlane_on_swimalne_post_save(sender, instance, created, **kwargs):
    """
    Set as project.default_swimlane if is the only one created.
    """
    if not created:
        return

    if instance._importing:
        return

    if instance.project.swimlanes.all().count() == 1:
        instance.project.default_swimlane = instance
        instance.project.save()


def create_swimlane_user_story_statuses_on_userstory_status_post_save(sender, instance, created, **kwargs):
    """
    Populate swimlanes with SwimlaneUserStoryStatus objects when a new UserStoryStatus is created.
    """
    if not created:
        return

    SwimlaneUserStoryStatus = apps.get_model("projects", "SwimlaneUserStoryStatus")
    copy_from_main_status = instance.project.swimlanes.count() == 1
    objects = (
        SwimlaneUserStoryStatus(
            swimlane=swimlane,
            status=instance,
            wip_limit=instance.wip_limit if copy_from_main_status else None
        )
    for swimlane in instance.project.swimlanes.all())

    SwimlaneUserStoryStatus.objects.bulk_create(objects)


## US statuses

def try_to_close_or_open_user_stories_when_edit_us_status(sender, instance, created, **kwargs):
    from taiga.projects.userstories import services

    for user_story in instance.user_stories.all():
        if services.calculate_userstory_is_closed(user_story):
            services.close_userstory(user_story)
        else:
            services.open_userstory(user_story)


## Task statuses

def try_to_close_or_open_user_stories_when_edit_task_status(sender, instance, created, **kwargs):
    from taiga.projects.userstories import services

    UserStory = apps.get_model("userstories", "UserStory")

    for user_story in UserStory.objects.filter(tasks__status=instance).distinct():
        if services.calculate_userstory_is_closed(user_story):
            services.close_userstory(user_story)
        else:
            services.open_userstory(user_story)


## Custom signals

issue_status_post_move_on_destroy = Signal()
