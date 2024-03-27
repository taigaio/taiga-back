# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import routers
from . import api


router = routers.DefaultRouter(trailing_slash=False)
router.register(r"feedback", api.FeedbackViewSet, base_name="feedback")
