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

from taiga.base.api import serializers

from . import models
from taiga.base.api import validators


class ApplicationValidator(validators.ModelValidator):
    class Meta:
        model = models.Application
        fields = ("id", "name", "web", "description", "icon_url")


class ApplicationTokenValidator(validators.ModelValidator):
    token = serializers.CharField(source="token", read_only=True)
    next_url = serializers.CharField(source="next_url", read_only=True)
    application = ApplicationValidator(read_only=True)

    class Meta:
        model = models.ApplicationToken
        fields = ("user", "id", "application", "auth_code", "next_url")


class AuthorizationCodeValidator(validators.ModelValidator):
    next_url = serializers.CharField(source="next_url", read_only=True)
    class Meta:
        model = models.ApplicationToken
        fields = ("auth_code", "state", "next_url")


class AccessTokenValidator(validators.ModelValidator):
    token = serializers.CharField(source="token", read_only=True)
    next_url = serializers.CharField(source="next_url", read_only=True)

    class Meta:
        model = models.ApplicationToken
        fields = ("token", )
