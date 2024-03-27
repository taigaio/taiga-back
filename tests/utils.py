# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
