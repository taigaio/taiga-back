# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from django.db import transaction
from django.db import connection

from . import models
import reversion


class UserStoriesService(object):
    @transaction.atomic
    def bulk_insert(self, project, user, data, callback_on_success=None):
        items = filter(lambda s: len(s) > 0,
                    map(lambda s: s.strip(), data.split("\n")))

        for item in items:
            obj = models.UserStory.objects.create(subject=item, project=project, owner=user,
                                                  status=project.default_us_status)
            if callback_on_success:
                callback_on_success(obj, True)

    @transaction.atomic
    def bulk_update_order(self, project, user, data):
        cursor = connection.cursor()

        sql = """
        prepare bulk_update_order as update userstories_userstory set "order" = $1
            where userstories_userstory.id = $2 and
                  userstories_userstory.project_id = $3;
        """

        cursor.execute(sql)
        for usid, usorder in data:
            cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                           (usorder, usid, project.id))
        cursor.close()
