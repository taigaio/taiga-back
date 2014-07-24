# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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
import functools
import json

from django.conf import settings
from django.db.models import signals


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


def set_settings(**new_settings):
    """Decorator for set django settings that will be only available during the
    wrapped-function execution.

    For example:
        @set_settings(FOO='bar')
        def myfunc():
            ...

       @set_settings(FOO='bar')
       class TestCase:
           ...
    """
    def decorator(testcase):
        if type(testcase) is type:
            namespace = {"OVERRIDE_SETTINGS": new_settings, "ORIGINAL_SETTINGS": {}}
            wrapper = type(testcase.__name__, (SettingsTestCase, testcase), namespace)
        else:
            @functools.wraps(testcase)
            def wrapper(*args, **kwargs):
                old_settings = override_settings(new_settings)
                try:
                    testcase(*args, **kwargs)
                finally:
                    override_settings(old_settings)

        return wrapper

    return decorator


def override_settings(new_settings):
    old_settings = {}
    for name, new_value in new_settings.items():
        old_settings[name] = getattr(settings, name, None)
        setattr(settings, name, new_value)
    return old_settings


class SettingsTestCase(object):
    @classmethod
    def setup_class(cls):
        cls.ORIGINAL_SETTINGS = override_settings(cls.OVERRIDE_SETTINGS)

    @classmethod
    def teardown_class(cls):
        override_settings(cls.ORIGINAL_SETTINGS)
        cls.OVERRIDE_SETTINGS.clear()

def _helper_test_http_method_responses(client, method, url, data, users, after_each_request=None):
    results = []
    for user in users:
        if user is None:
            client.logout()
        else:
            client.login(user)
        if data:
            response = getattr(client, method)(url, data, content_type="application/json")
        else:
            response = getattr(client, method)(url)
        if response.status_code == 400:
            print(response.content)

        results.append(response)

        if after_each_request is not None:
            after_each_request()
    return results

def helper_test_http_method(client, method, url, data, users, after_each_request=None):
    responses = _helper_test_http_method_responses(client, method, url, data, users, after_each_request)
    return list(map(lambda r: r.status_code, responses))


def helper_test_http_method_and_count(client, method, url, data, users, after_each_request=None):
    responses = _helper_test_http_method_responses(client, method, url, data, users, after_each_request)
    return list(map(lambda r: (r.status_code, len(json.loads(r.content.decode('utf-8')))), responses))

def helper_test_http_method_and_keys(client, method, url, data, users, after_each_request=None):
    responses = _helper_test_http_method_responses(client, method, url, data, users, after_each_request)
    return list(map(lambda r: (r.status_code, set(json.loads(r.content.decode('utf-8')).keys())), responses))
