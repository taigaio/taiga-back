# -*- coding: utf-8 -*-
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
