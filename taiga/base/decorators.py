# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

import warnings


# Rest Framework 2.4 backport some decorators.

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


def link(**kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail GET requests.
    """
    msg = 'link is pending deprecation. Use detail_route instead.'
    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

    def decorator(func):
        func.bind_to_methods = ['get']
        func.detail = True
        func.permission_classes = kwargs.get('permission_classes', [])
        func.kwargs = kwargs
        return func

    return decorator


def action(methods=['post'], **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail POST requests.
    """
    msg = 'action is pending deprecation. Use detail_route instead.'
    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

    def decorator(func):
        func.bind_to_methods = methods
        func.detail = True
        func.permission_classes = kwargs.get('permission_classes', [])
        func.kwargs = kwargs
        return func

    return decorator
