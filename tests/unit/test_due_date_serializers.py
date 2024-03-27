# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import datetime as dt
from unittest import mock

import pytest

from django.utils import timezone

from taiga.projects.due_dates.serializers import DueDateSerializerMixin

@pytest.mark.parametrize('due_date, is_closed, expected', [
    (None, False, 'not_set'),
    (dt.date(2100, 1, 1), True, 'no_longer_applicable'),
    (dt.date(2100, 12, 31), False, 'set'),
    (dt.date(2000, 1, 1), False, 'past_due'),
    (timezone.now().date(), False, 'due_soon'),
])
def test_due_date_status(due_date, is_closed, expected):
    serializer = DueDateSerializerMixin()
    obj_status = mock.MagicMock(is_closed=is_closed)
    obj = mock.MagicMock(due_date=due_date, status=obj_status)
    status = serializer.get_due_date_status(obj)
    assert status == expected
