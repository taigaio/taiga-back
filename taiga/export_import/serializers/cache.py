# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.users import models as users_models

_cache_user_by_pk = {}
_cache_user_by_email = {}
_custom_tasks_attributes_cache = {}
_custom_issues_attributes_cache = {}
_custom_userstories_attributes_cache = {}
_custom_epics_attributes_cache = {}
_tasks_statuses_cache = {}
_issues_statuses_cache = {}
_userstories_statuses_cache = {}
_epics_statuses_cache = {}


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
