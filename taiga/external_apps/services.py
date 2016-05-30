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


from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404

from django.apps import apps
from django.utils.translation import ugettext as _

from . import encryption

import json

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


def cypher_token(application_token:object) -> str:
    content = {
        "token": application_token.token
    }

    return encryption.encrypt(json.dumps(content), application_token.application.key)
