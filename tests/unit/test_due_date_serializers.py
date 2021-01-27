# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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
