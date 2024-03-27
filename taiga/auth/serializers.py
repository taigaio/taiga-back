# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# The code is partially taken (and modified) from djangorestframework-simplejwt v. 4.7.1
# (https://github.com/jazzband/djangorestframework-simplejwt/tree/5997c1aee8ad5182833d6b6759e44ff0a704edb4)
# that is licensed under the following terms:
#
#   Copyright 2017 David Sanders
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import bleach
import re

from django.core import validators as core_validators
from django.utils.translation import gettext as _

from taiga.base.api import serializers
from taiga.base.exceptions import ValidationError

from .services import login, refresh_token, verify_token


class TokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        authenticate_kwargs = {
            'username': attrs['username'],
            'password': attrs['password'],
        }

        return login(**authenticate_kwargs)


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        return refresh_token(attrs['refresh'])


class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        return verify_token(attrs['token'])



class BaseRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=36)
    email = serializers.EmailField(max_length=255)
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=6)

    def validate_username(self, attrs, source):
        value = attrs[source]
        validator = core_validators.RegexValidator(re.compile(r'^[\w.-]+$'), _("invalid username"), "invalid")

        try:
            validator(value)
        except ValidationError:
            raise ValidationError(_("Required. 255 characters or fewer. Letters, numbers "
                                    "and /./-/_ characters'"))
        return attrs

    def validate_full_name(self, attrs, source):
        value = attrs[source]
        if value != bleach.clean(value):
            raise ValidationError(_("Invalid full name"))

        if re.search(r"http[s]?:", value):
            raise ValidationError(_("Invalid full name"))

        return attrs


class PublicRegisterSerializer(BaseRegisterSerializer):
    pass


class PrivateRegisterSerializer(BaseRegisterSerializer):
    token = serializers.CharField(max_length=255, required=True)
