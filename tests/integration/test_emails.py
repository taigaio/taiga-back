# -*- coding: utf-8 -*-
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
