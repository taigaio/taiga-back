# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.db import IntegrityError
from django.utils.translation import gettext as _

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
