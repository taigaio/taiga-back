# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import enum

from django.utils.translation import gettext_lazy as _


class HistoryType(enum.IntEnum):
    change = 1
    create = 2
    delete = 3


HISTORY_TYPE_CHOICES = ((HistoryType.change, _("Change")),
                        (HistoryType.create, _("Create")),
                        (HistoryType.delete, _("Delete")))
