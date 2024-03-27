# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import response
from taiga.base.api import viewsets

from . import permissions
from . import validators
from . import services

import copy


class FeedbackViewSet(viewsets.ViewSet):
    permission_classes = (permissions.FeedbackPermission,)
    validator_class = validators.FeedbackEntryValidator

    def create(self, request, **kwargs):
        self.check_permissions(request, "create", None)

        data = copy.deepcopy(request.DATA)
        data.update({"full_name": request.user.get_full_name(),
                     "email": request.user.email})

        validator = self.validator_class(data=data)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        self.object = validator.save(force_insert=True)

        extra = {
            "HTTP_HOST":  request.headers.get("host", None),
            "HTTP_REFERER": request.headers.get("referer", None),
            "HTTP_USER_AGENT": request.headers.get("user-agent", None),
        }
        services.send_feedback(self.object, extra, reply_to=[request.user.email])

        return response.Ok(validator.data)
