# Copyright (C) 2015 Taiga Agile LLC <support@taiga.io>
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

from contextlib import closing

from django.apps import apps
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from collections import OrderedDict


def get_users_stats():
    model = apps.get_model("users", "User")
    queryset =  model.objects.filter(is_active=True, is_system=False)
    stats = OrderedDict()

    # Total
    stats["total"] = queryset.count()

    # Average last 7 days
    today = timezone.now()
    seven_days_ago = today-timedelta(days=7)
    stats["average_last_seven_days"] = (queryset.filter(date_joined__range=(seven_days_ago, today))
                                                .count()) / 7

    # Graph: users last year
    a_year_ago = timezone.now() - timedelta(days=365)
    sql_query = """
      SELECT date_trunc('week', "filtered_users"."date_joined") AS "week",
             count(*)
        FROM (SELECT *
                FROM "users_user"
               WHERE "users_user"."is_active" = TRUE
                 AND "users_user"."is_system" = FALSE
                 AND "users_user"."date_joined" >= %s) AS "filtered_users"
    GROUP BY "week"
    ORDER BY "week";
    """
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql_query, [a_year_ago])
        rows = cursor.fetchall()

    counts_last_year_per_week = OrderedDict()
    sumatory = queryset.filter(date_joined__lt=rows[0][0]).count()
    for row in rows:
        sumatory += row[1]
        counts_last_year_per_week[str(row[0].date())] = sumatory

    stats["counts_last_year_per_week"] = counts_last_year_per_week

    return stats


def get_projects_stats():
    model = apps.get_model("projects", "Project")
    queryset =  model.objects.all()
    stats = OrderedDict()

    stats["total"] = queryset.count()

    today = timezone.now()
    seven_days_ago = today-timedelta(days=7)
    stats["average_last_seven_days"] = (queryset.filter(created_date__range=(seven_days_ago, today))
                                                 .count()) / 7

    stats["total_with_backlog"] = (queryset.filter(is_backlog_activated=True,
                                                   is_kanban_activated=False)
                                           .count())
    stats["percent_with_backlog"] = stats["total_with_backlog"] * 100 / stats["total"]

    stats["total_with_kanban"] = (queryset.filter(is_backlog_activated=False,
                                                  is_kanban_activated=True)
                                          .count())
    stats["percent_with_kanban"] = stats["total_with_kanban"] * 100 / stats["total"]

    stats["total_with_backlog_and_kanban"] = (queryset.filter(is_backlog_activated=True,
                                                              is_kanban_activated=True)
                                                      .count())
    stats["percent_with_backlog_and_kanban"] = stats["total_with_backlog_and_kanban"] * 100 / stats["total"]

    return stats


def get_user_stories_stats():
    model = apps.get_model("userstories", "UserStory")
    queryset =  model.objects.all()
    stats = OrderedDict()

    stats["total"] = queryset.count()

    today = timezone.now()
    seven_days_ago = today-timedelta(days=7)
    stats["average_last_seven_days"] = (queryset.filter(created_date__range=(seven_days_ago, today))
                                                 .count()) / 7
    return stats
