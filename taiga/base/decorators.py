# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django_pglocks import advisory_lock


def detail_route(methods=['get'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail requests.
    """
    def decorator(func):
        func.bind_to_methods = methods
        func.detail = True
        func.permission_classes = kwargs.get('permission_classes', [])
        func.kwargs = kwargs
        return func
    return decorator


def list_route(methods=['get'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for list requests.
    """
    def decorator(func):
        func.bind_to_methods = methods
        func.detail = False
        func.permission_classes = kwargs.get('permission_classes', [])
        func.kwargs = kwargs
        return func
    return decorator


def model_pk_lock(func):
    """
    This decorator is designed to be used in ModelViewsets methods to lock them based
    on the model and the id of the selected object.
    """
    def decorator(self, *args, **kwargs):
        from taiga.base.utils.db import get_typename_for_model_class
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        tn = get_typename_for_model_class(self.get_queryset().model)
        key = "{0}:{1}".format(tn, pk)

        with advisory_lock(key):
            return func(self, *args, **kwargs)

    return decorator
