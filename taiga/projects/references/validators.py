# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError


class ResolverValidator(validators.Validator):
    project = serializers.CharField(max_length=512, required=True)
    milestone = serializers.CharField(max_length=512, required=False)
    epic = serializers.IntegerField(required=False)
    us = serializers.IntegerField(required=False)
    task = serializers.IntegerField(required=False)
    issue = serializers.IntegerField(required=False)
    wikipage = serializers.CharField(max_length=512, required=False)
    ref = serializers.CharField(max_length=512, required=False)

    def validate(self, attrs):
        if "ref" in attrs:
            if "epic" in attrs:
                raise ValidationError("'epic' param is incompatible with 'ref' in the same request")
            if "us" in attrs:
                raise ValidationError("'us' param is incompatible with 'ref' in the same request")
            if "task" in attrs:
                raise ValidationError("'task' param is incompatible with 'ref' in the same request")
            if "issue" in attrs:
                raise ValidationError("'issue' param is incompatible with 'ref' in the same request")
            if "wikipage" in attrs:
                raise ValidationError("'wikipage' param is incompatible with 'ref' in the same request")

        return attrs
