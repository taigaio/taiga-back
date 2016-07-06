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

from django.core import validators as core_validators
from django.utils.translation import ugettext_lazy as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.base.fields import PgArrayField

from .models import User, Role

import re


class RoleExistsValidator:
    def validate_role_id(self, attrs, source):
        value = attrs[source]
        if not Role.objects.filter(pk=value).exists():
            msg = _("There's no role with that id")
            raise ValidationError(msg)
        return attrs


######################################################
# User
######################################################
class UserValidator(validators.ModelValidator):
    class Meta:
        model = User
        fields = ("username", "full_name", "color", "bio", "lang",
                  "theme", "timezone", "is_active")

    def validate_username(self, attrs, source):
        value = attrs[source]
        validator = core_validators.RegexValidator(re.compile('^[\w.-]+$'), _("invalid username"),
                                                   _("invalid"))

        try:
            validator(value)
        except ValidationError:
            raise ValidationError(_("Required. 255 characters or fewer. Letters, "
                                    "numbers and /./-/_ characters'"))

        if (self.object and
                self.object.username != value and
                User.objects.filter(username=value).exists()):
            raise ValidationError(_("Invalid username. Try with a different one."))

        return attrs


class UserAdminValidator(UserValidator):
    class Meta:
        model = User
        # IMPORTANT: Maintain the UserSerializer Meta up to date
        # with this info (including here the email)
        fields = ("username", "full_name", "color", "bio", "lang",
                  "theme", "timezone", "is_active", "email")


class RecoveryValidator(validators.Validator):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=6)


class ChangeEmailValidator(validators.Validator):
    email_token = serializers.CharField(max_length=200)


class CancelAccountValidator(validators.Validator):
    cancel_token = serializers.CharField(max_length=200)


######################################################
# Role
######################################################

class RoleValidator(validators.ModelValidator):
    permissions = PgArrayField(required=False)

    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'computable', 'project', 'order')
        i18n_fields = ("name",)


class ProjectRoleValidator(validators.ModelValidator):
    class Meta:
        model = Role
        fields = ('id', 'name', 'slug', 'order', 'computable')
