# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import django.dispatch


user_change_email = django.dispatch.Signal()    # providing_args=["user", "old_email", "new_email"]
user_cancel_account = django.dispatch.Signal()  # providing_args=["user", "request_data"]
