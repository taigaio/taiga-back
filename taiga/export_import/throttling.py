# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import throttling


class ImportModeRateThrottle(throttling.UserRateThrottle):
    scope = "import-mode"


class ImportDumpModeRateThrottle(throttling.UserRateThrottle):
    scope = "import-dump-mode"
