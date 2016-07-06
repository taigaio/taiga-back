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
from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError

import re


class BaseRegisterValidator(validators.Validator):
    full_name = serializers.CharField(max_length=256)
    email = serializers.EmailField(max_length=255)
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=4)

    def validate_username(self, attrs, source):
        value = attrs[source]
        validator = core_validators.RegexValidator(re.compile('^[\w.-]+$'), _("invalid username"), "invalid")

        try:
            validator(value)
        except ValidationError:
            raise ValidationError(_("Required. 255 characters or fewer. Letters, numbers "
                                    "and /./-/_ characters'"))
        return attrs


class PublicRegisterValidator(BaseRegisterValidator):
    pass


class PrivateRegisterForNewUserValidator(BaseRegisterValidator):
    token = serializers.CharField(max_length=255, required=True)


class PrivateRegisterForExistingUserValidator(validators.Validator):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=4)
    token = serializers.CharField(max_length=255, required=True)
