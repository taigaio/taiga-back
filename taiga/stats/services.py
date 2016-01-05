# Copyright (C) 2014-2016 Taiga Agile LLC <support@taiga.io>
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
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone

from datetime import timedelta
from collections import OrderedDict


def get_users_stats():
    model = apps.get_model("users", "User")
    queryset =  model.objects.filter(is_active=True, is_system=False)
    stats = OrderedDict()

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    seven_days_ago = yesterday - timedelta(days=7)
    a_year_ago = today - timedelta(days=365)

    stats["total"] = queryset.count()
    stats["today"] = queryset.filter(date_joined__year=today.year,
                                     date_joined__month=today.month,
                                     date_joined__day=today.day).count()
    stats["average_last_seven_days"] = (queryset.filter(date_joined__range=(seven_days_ago, yesterday))
                                                .count()) / 7
    stats["average_last_five_working_days"] = (queryset.filter(date_joined__range=(seven_days_ago, yesterday))
                                                       .exclude(Q(date_joined__week_day=1) |
                                                                Q(date_joined__week_day=7))
                                                       .count()) / 5

    # Graph: users last year
    # increments ->
    #   SELECT date_trunc('week', "filtered_users"."date_joined") AS "week",
    #          count(*)
    #     FROM (SELECT *
    #             FROM "users_user"
    #            WHERE "users_user"."is_active" = TRUE
    #              AND "users_user"."is_system" = FALSE
    #              AND "users_user"."date_joined" >= %s) AS "filtered_users"
    # GROUP BY "week"
    # ORDER BY "week";
    increments = (queryset.filter(date_joined__gte=a_year_ago)
                          .extra({"week": "date_trunc('week', date_joined)"})
                          .values("week")
                          .order_by("week")
                          .annotate(count=Count("id")))

    counts_last_year_per_week = OrderedDict()
    sumatory = queryset.filter(date_joined__lt=increments[0]["week"]).count()
    for inc in increments:
        sumatory += inc["count"]
        counts_last_year_per_week[str(inc["week"].date())] = sumatory

    stats["counts_last_year_per_week"] = counts_last_year_per_week

    return stats


def get_projects_stats():
    model = apps.get_model("projects", "Project")
    queryset =  model.objects.all()
    stats = OrderedDict()

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    seven_days_ago = yesterday - timedelta(days=7)

    stats["total"] = queryset.count()
    stats["today"] = queryset.filter(created_date__year=today.year,
                                     created_date__month=today.month,
                                     created_date__day=today.day).count()
    stats["average_last_seven_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                                 .count()) / 7
    stats["average_last_five_working_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                                       .exclude(Q(created_date__week_day=1) |
                                                                Q(created_date__week_day=7))
                                                       .count()) / 5

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

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    seven_days_ago = yesterday - timedelta(days=7)

    stats["total"] = queryset.count()
    stats["today"] = queryset.filter(created_date__year=today.year,
                                     created_date__month=today.month,
                                     created_date__day=today.day).count()
    stats["average_last_seven_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                                 .count()) / 7
    stats["average_last_five_working_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                                       .exclude(Q(created_date__week_day=1) |
                                                                Q(created_date__week_day=7))
                                                       .count()) / 5

    return stats
