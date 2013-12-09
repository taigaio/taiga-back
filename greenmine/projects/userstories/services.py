# -*- coding: utf-8 -*-

from django.db import transaction
from django.db import connection

from . import models


class UserStoriesService(object):
    @transaction.atomic
    def bulk_insert(self, project, user, data):
        items = filter(lambda s: len(s) > 0,
                    map(lambda s: s.strip(), data.split("\n")))

        for item in items:
            models.UserStory.objects.create(subject=item, project=project, owner=user,
                                            status=project.default_us_status)

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
