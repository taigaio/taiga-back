# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404

from django.apps import apps
from django.utils.translation import gettext as _


def get_user_for_application_token(token:str) -> object:
    """
    Given an application token it tries to find an associated user
    """
    app_token = apps.get_model("external_apps", "ApplicationToken").objects.filter(token=token).first()
    if not app_token:
        raise exc.NotAuthenticated(_("Invalid token"))
    return app_token.user


def authorize_token(application_id:int, user:object, state:str) -> object:
    ApplicationToken = apps.get_model("external_apps", "ApplicationToken")
    Application = apps.get_model("external_apps", "Application")
    application = get_object_or_404(Application, id=application_id)
    token, _ = ApplicationToken.objects.get_or_create(user=user, application=application)
    token.update_auth_code()
    token.state = state
    token.save()
    return token
