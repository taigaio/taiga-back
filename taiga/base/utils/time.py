# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import time


def timestamp_ms():
    """Ruturn timestamp in milisecond."""
    return int(time.time() * 1000)


def timestamp_mics():
    """Return timestamp in microseconds."""
    return int(time.time() * 1000000)
