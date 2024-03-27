# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.projects.settings.utils import get_allowed_sections

from . import models


class UserProjectSettingsValidator(validators.ModelValidator):

    class Meta:
        model = models.UserProjectSettings
        read_only_fields = ('id', 'created_at', 'modified_at', 'project',
                            'user')

    def validate_homepage(self, attrs, source):
        if attrs[source] not in get_allowed_sections(self.object):
            msg = _("You don't have access to this section")
            raise ValidationError(msg)
        return attrs
