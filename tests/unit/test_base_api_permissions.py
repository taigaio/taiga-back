# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import (AllowAny as TruePermissionComponent,
                                        DenyAll as FalsePermissionComponent)


def test_permission_component_composition():
    assert (TruePermissionComponent() | TruePermissionComponent()).check_permissions(None, None, None)
    assert (TruePermissionComponent() | FalsePermissionComponent()).check_permissions(None, None, None)
    assert (FalsePermissionComponent() | TruePermissionComponent()).check_permissions(None, None, None)
    assert not (FalsePermissionComponent() | FalsePermissionComponent()).check_permissions(None, None, None)

    assert (TruePermissionComponent() & TruePermissionComponent()).check_permissions(None, None, None)
    assert not (TruePermissionComponent() & FalsePermissionComponent()).check_permissions(None, None, None)
    assert not (FalsePermissionComponent() & TruePermissionComponent()).check_permissions(None, None, None)
    assert not (FalsePermissionComponent() & FalsePermissionComponent()).check_permissions(None, None, None)

    assert (~FalsePermissionComponent()).check_permissions(None, None, None)
    assert not (~TruePermissionComponent()).check_permissions(None, None, None)
