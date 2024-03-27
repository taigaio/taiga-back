# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
