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
from django.utils.translation import ugettext_lazy as _

from taiga.base.api import serializers
from taiga.base.fields import PgArrayField

from .models import User, Role
from .services import get_photo_or_gravatar_url, get_big_photo_or_gravatar_url

import re


######################################################
## User
######################################################

class UserSerializer(serializers.ModelSerializer):
    full_name_display = serializers.SerializerMethodField("get_full_name_display")
    photo = serializers.SerializerMethodField("get_photo")
    big_photo = serializers.SerializerMethodField("get_big_photo")

    class Meta:
        model = User
        # IMPORTANT: Maintain the UserAdminSerializer Meta up to date
        # with this info (including there the email)
        fields = ("id", "username", "full_name", "full_name_display",
                  "color", "bio", "lang", "timezone", "is_active",
                  "photo", "big_photo")
        read_only_fields = ("id",)

    def validate_username(self, attrs, source):
        value = attrs[source]
        validator = validators.RegexValidator(re.compile('^[\w.-]+$'), _("invalid username"),
                                              _("invalid"))

        try:
            validator(value)
        except ValidationError:
            raise serializers.ValidationError(_("Required. 255 characters or fewer. Letters, "
                                                "numbers and /./-/_ characters'"))

        if (self.object and
                self.object.username != value and
                User.objects.filter(username=value).exists()):
            raise serializers.ValidationError(_("Invalid username. Try with a different one."))

        return attrs

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_photo_or_gravatar_url(user)

    def get_big_photo(self, user):
        return get_big_photo_or_gravatar_url(user)


class UserAdminSerializer(UserSerializer):
    class Meta:
        model = User
        # IMPORTANT: Maintain the UserSerializer Meta up to date
        # with this info (including here the email)
        fields = ("id", "username", "full_name", "full_name_display", "email",
                  "color", "bio", "lang", "timezone", "is_active", "photo",
                  "big_photo")
        read_only_fields = ("id", "email")


class RecoverySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=6)


class ChangeEmailSerializer(serializers.Serializer):
    email_token = serializers.CharField(max_length=200)


class CancelAccountSerializer(serializers.Serializer):
    cancel_token = serializers.CharField(max_length=200)


######################################################
## Role
######################################################

class RoleSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField("get_members_count")
    permissions = PgArrayField(required=False)

    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'computable', 'project', 'order', 'members_count')
        i18n_fields = ("name",)

    def get_members_count(self, obj):
        return obj.memberships.count()


class ProjectRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'slug', 'order', 'computable')
        i18n_fields = ("name",)
