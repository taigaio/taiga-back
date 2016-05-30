# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.apps import apps
from django.conf import settings

from taiga.projects.services.tags_colors import update_project_tags_colors_handler, remove_unused_tags
from taiga.projects.notifications.services import create_notify_policy_if_not_exists
from taiga.base.utils.db import get_typename_for_model_class

from easy_thumbnails.files import get_thumbnailer


####################################
# Signals over project items
####################################

## TAGS

def tags_normalization(sender, instance, **kwargs):
    if isinstance(instance.tags, (list, tuple)):
        instance.tags = list(map(str.lower, instance.tags))


def update_project_tags_when_create_or_edit_taggable_item(sender, instance, **kwargs):
    update_project_tags_colors_handler(instance)


def update_project_tags_when_delete_taggable_item(sender, instance, **kwargs):
    remove_unused_tags(instance.project)
    instance.project.save()

def membership_post_delete(sender, instance, using, **kwargs):
    instance.project.update_role_points()


## Notify policy

def create_notify_policy(sender, instance, using, **kwargs):
    if instance.user:
        create_notify_policy_if_not_exists(instance.project, instance.user)


## Project attributes

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
