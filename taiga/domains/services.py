"""
This module contains a domain logic for domains application.
"""

from django.db.models.loading import get_model
from django.db import transaction as tx
from django.db import IntegrityError

from taiga.base import exceptions as exc


def is_user_exists_on_domain(domain, user) -> bool:
    """
    Checks if user is alredy exists on domain.
    """
    return domain.members.filter(user=user).exists()


def is_public_register_enabled_for_domain(domain) -> bool:
    """
    Checks if a specified domain have public register
    activated.

    The implementation is very simple but it encapsulates
    request attribute access into more semantic function
    call.
    """
    return domain.public_register


@tx.atomic
def create_domain_member(domain, user):
    """
    Given a domain and user, add user as member to
    specified domain.

    :returns: DomainMember
    """
    domain_member_model = get_model("domains", "DomainMember")

    try:
        domain_member = domain_member_model(domain=domain, user=user,
                                            email=user.email, is_owner=False,
                                            is_staff=False)
        domain_member.save()
    except IntegrityError:
        raise exc.IntegrityError("User is already member in a site")

    return domain_member
