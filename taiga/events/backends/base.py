# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import abc
import importlib

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


class BaseEventsPushBackend(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def emit_event(self, message:str, *, routing_key:str, channel:str="events"):
        pass


def load_class(path):
    """
    Load class from path.
    """

    mod_name, klass_name = path.rsplit('.', 1)

    try:
        mod = importlib.import_module(mod_name)
    except AttributeError as e:
        raise ImproperlyConfigured('Error importing {0}: "{1}"'.format(mod_name, e))

    try:
        klass = getattr(mod, klass_name)
    except AttributeError:
        raise ImproperlyConfigured('Module "{0}" does not define a "{1}" class'.format(mod_name, klass_name))

    return klass


def get_events_backend(path:str=None, options:dict=None):
    if path is None:
        path = getattr(settings, "EVENTS_PUSH_BACKEND", None)

        if path is None:
            raise ImproperlyConfigured("Events push system not configured")

    if options is None:
        options = getattr(settings, "EVENTS_PUSH_BACKEND_OPTIONS", {})

    cls = load_class(path)
    return cls(**options)
