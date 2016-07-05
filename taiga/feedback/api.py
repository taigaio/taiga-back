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
            "HTTP_HOST":  request.META.get("HTTP_HOST", None),
            "HTTP_REFERER": request.META.get("HTTP_REFERER", None),
            "HTTP_USER_AGENT": request.META.get("HTTP_USER_AGENT", None),
        }
        services.send_feedback(self.object, extra, reply_to=[request.user.email])

        return response.Ok(validator.data)
