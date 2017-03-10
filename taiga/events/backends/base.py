# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
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
