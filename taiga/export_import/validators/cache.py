# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.users import models as users_models

_cache_user_by_pk = {}
_cache_user_by_email = {}
_custom_tasks_attributes_cache = {}
_custom_issues_attributes_cache = {}
_custom_epics_attributes_cache = {}
_custom_userstories_attributes_cache = {}


def cached_get_user_by_pk(pk):
    if pk not in _cache_user_by_pk:
        try:
            _cache_user_by_pk[pk] = users_models.User.objects.get(pk=pk)
        except Exception:
            _cache_user_by_pk[pk] = users_models.User.objects.get(pk=pk)
    return _cache_user_by_pk[pk]

def cached_get_user_by_email(email):
    if email not in _cache_user_by_email:
        try:
            _cache_user_by_email[email] = users_models.User.objects.get(email=email)
        except Exception:
            _cache_user_by_email[email] = users_models.User.objects.get(email=email)
    return _cache_user_by_email[email]
