# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from django.db.models import signals

DUMMY_BMP_DATA = b'BM:\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x04\x00\x00\x00\x13\x0b\x00\x00\x13\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


def signals_switch():
    pre_save = signals.pre_save.receivers
    post_save = signals.post_save.receivers

    def disconnect():
        signals.pre_save.receivers = []
        signals.post_save.receivers = []

    def reconnect():
        signals.pre_save.receivers = pre_save
        signals.post_save.receivers = post_save

    return disconnect, reconnect


disconnect_signals, reconnect_signals = signals_switch()


def _helper_test_http_method_responses(client, method, url, data, users, after_each_request=None,
                                       content_type="application/json"):
    results = []

    for user in users:
        if user is None:
            client.logout()
        else:
            client.login(user)
        if data:
            response = getattr(client, method)(url, data, content_type=content_type)
        else:
            response = getattr(client, method)(url)
        #if response.status_code >= 400:
        #    print("Response content:", response.content)

        results.append(response)

        if after_each_request is not None:
            after_each_request()
    return results


def helper_test_http_method(client, method, url, data, users, after_each_request=None,
                            content_type="application/json"):
    responses = _helper_test_http_method_responses(client, method, url, data, users, after_each_request,
                                                   content_type=content_type)
    return list(map(lambda r: r.status_code, responses))


def helper_test_http_method_and_count(client, method, url, data, users, after_each_request=None):
    responses = _helper_test_http_method_responses(client, method, url, data, users, after_each_request)
    return list(map(lambda r: (r.status_code, len(r.data) if isinstance(r.data, list) and 200 <= r.status_code < 300 else 0), responses))


def helper_test_http_method_and_keys(client, method, url, data, users, after_each_request=None):
    responses = _helper_test_http_method_responses(client, method, url, data, users, after_each_request)
    return list(map(lambda r: (r.status_code, set(r.data.keys() if isinstance(r.data, dict) and 200 <= r.status_code < 300 else [])), responses))
