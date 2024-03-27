# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# This makes all code that import services works and
# is not the baddest practice ;)

from .render import render_project
from . import render

from .store import store_project_from_dict
from . import store

from .validations import has_available_slot_for_new_project
from . import validations
