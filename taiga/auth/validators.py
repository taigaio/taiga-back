# -*- coding: utf-8 -*-
import bleach

from django.core import validators as core_validators
from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError

import re


class BaseRegisterValidator(validators.Validator):
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


class PublicRegisterValidator(BaseRegisterValidator):
    pass


class PrivateRegisterValidator(BaseRegisterValidator):
    token = serializers.CharField(max_length=255, required=True)
