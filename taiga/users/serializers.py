# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from django.core import validators
from django.core.exceptions import ValidationError

from rest_framework import serializers

from .models import User
from .services import get_photo_or_gravatar_url, get_big_photo_or_gravatar_url

import re


class UserSerializer(serializers.ModelSerializer):
    full_name_display = serializers.SerializerMethodField("get_full_name_display")
    photo = serializers.SerializerMethodField("get_photo")
    big_photo = serializers.SerializerMethodField("get_big_photo")

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "full_name_display", "email",
                  "github_id", "color", "bio", "default_language",
                  "default_timezone", "is_active", "photo", "big_photo")
        read_only_fields = ("id", "email", "github_id")

    def validate_username(self, attrs, source):
        value = attrs[source]
        validator = validators.RegexValidator(re.compile('^[\w.-]+$'), "invalid username", "invalid")

        try:
            validator(value)
        except ValidationError:
            raise serializers.ValidationError("Required. 255 characters or fewer. Letters, numbers "
                                              "and /./-/_ characters'")

        if self.object and self.object.username != value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Invalid username. Try with a different one.")

        return attrs

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_photo_or_gravatar_url(user)

    def get_big_photo(self, user):
        return get_big_photo_or_gravatar_url(user)


class RecoverySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=6)


class ChangeEmailSerializer(serializers.Serializer):
    email_token = serializers.CharField(max_length=200)


class CancelAccountSerializer(serializers.Serializer):
    cancel_token = serializers.CharField(max_length=200)
