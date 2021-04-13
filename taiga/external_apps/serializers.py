# -*- coding: utf-8 -*-
from taiga.base.api import serializers
from taiga.base.fields import Field

from . import models
from . import services

from django.utils.translation import ugettext as _


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
