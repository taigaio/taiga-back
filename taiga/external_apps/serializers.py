# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import Field

from . import models
from . import services

from django.utils.translation import gettext as _


class ApplicationSerializer(serializers.LightSerializer):
    id = Field()
    name = Field()
    web = Field()
    description = Field()
    icon_url = Field()


class ApplicationTokenSerializer(serializers.LightSerializer):
    id = Field()
    user = Field(attr="user_id")
    application = ApplicationSerializer()
    auth_code = Field()
    next_url = Field()


class AuthorizationCodeSerializer(serializers.LightSerializer):
    state = Field()
    auth_code = Field()
    next_url = Field()


class AccessTokenSerializer(serializers.LightSerializer):
    token = Field()
