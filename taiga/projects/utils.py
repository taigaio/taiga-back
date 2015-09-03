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

from django.apps import apps

def attach_notify_level_to_queryset(queryset, user, as_field="notify_level"):
    """Attach notify level to each object of the queryset.

    :param queryset: A Django queryset object.
    :param as_field: Attach the notify level as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    if user.is_authenticated():
        model = queryset.model
        sql = ("""SELECT notifications_notifypolicy.notify_level
                    FROM notifications_notifypolicy
                   WHERE notifications_notifypolicy.user_id = {user_id}
                     AND notifications_notifypolicy.project_id = {tbl}.id""")
        sql = sql.format(user_id=user.id, tbl=model._meta.db_table)
    else:
        sql = "SELECT CAST(NULL as text)"

    qs = queryset.extra(select={as_field: sql})
    return qs
