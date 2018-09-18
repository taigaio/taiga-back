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

from django.apps import apps
from django.db import IntegrityError
from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.projects.settings.choices import Section


def user_project_settings_exists(project, user) -> bool:
    """
    Check if policy exists for specified project
    and user.
    """
    model_cls = apps.get_model("settings", "UserProjectSettings")
    qs = model_cls.objects.filter(project=project,
                                  user=user)
    return qs.exists()


def create_user_project_settings(project, user, homepage=Section.timeline):
    """
    Given a project and user, create notification policy for it.
    """
    model_cls = apps.get_model("settings", "UserProjectSettings")
    try:
        return model_cls.objects.create(project=project,
                                        user=user,
                                        homepage=homepage)
    except IntegrityError as e:
        raise exc.IntegrityError(
            _("Notify exists for specified user and project")) from e


def create_user_project_settings_if_not_exists(project, user,
                                               homepage=Section.timeline):
    """
    Given a project and user, create notification policy for it.
    """
    model_cls = apps.get_model("settings", "UserProjectSettings")
    try:
        result = model_cls.objects.get_or_create(
            project=project,
            user=user,
            defaults={"homepage": homepage}
        )
        return result[0]
    except IntegrityError as e:
        raise exc.IntegrityError(
            _("Notify exists for specified user and project")) from e
