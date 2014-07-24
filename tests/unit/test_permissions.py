from taiga.permissions import service
from taiga.users.models import Role

import pytest


def test_role_has_perm():
    role = Role()
    role.permissions = ["test"]
    assert service.role_has_perm(role, "test")
    assert service.role_has_perm(role, "false") == False
