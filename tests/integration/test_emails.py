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
import pytest

from django.core.management import call_command

from .. import factories as f


@pytest.mark.django_db
def test_emails():
    # Membership invitation
    m = f.MembershipFactory.create()
    m.user = None
    m.save()

    # Regular membership
    f.MembershipFactory.create()

    # f.UserFactory.create()
    call_command('test_emails', 'none@example.test')
