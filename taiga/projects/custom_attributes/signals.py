# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
