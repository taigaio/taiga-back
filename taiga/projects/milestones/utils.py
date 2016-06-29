# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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
from django.db.models import Prefetch

from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.notifications.utils import attach_total_watchers_to_queryset
from taiga.projects.notifications.utils import attach_is_watcher_to_queryset
from taiga.projects.userstories import utils as userstories_utils
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.votes.utils import attach_is_voter_to_queryset


def attach_total_points(queryset, as_field="total_points_attr"):
    """Attach total of point values to each object of the queryset.

    :param queryset: A Django milestones queryset object.
    :param as_field: Attach the points as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """SELECT SUM(projects_points.value)
                    FROM userstories_rolepoints
                    INNER JOIN userstories_userstory ON userstories_userstory.id = userstories_rolepoints.user_story_id
                    INNER JOIN projects_points ON userstories_rolepoints.points_id = projects_points.id
                    WHERE userstories_userstory.milestone_id = {tbl}.id"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_closed_points(queryset, as_field="closed_points_attr"):
    """Attach total of closed point values to each object of the queryset.

    :param queryset: A Django milestones queryset object.
    :param as_field: Attach the points as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """SELECT SUM(projects_points.value)
                    FROM userstories_rolepoints
                    INNER JOIN userstories_userstory ON userstories_userstory.id = userstories_rolepoints.user_story_id
                    INNER JOIN projects_points ON userstories_rolepoints.points_id = projects_points.id
                    WHERE userstories_userstory.milestone_id = {tbl}.id AND userstories_userstory.is_closed=True"""

    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_extra_info(queryset, user=None):
    # Userstories prefetching
    UserStory = apps.get_model("userstories", "UserStory")
    us_queryset = UserStory.objects.select_related("milestone",
                                                   "project",
                                                   "status",
                                                   "owner",
                                                   "assigned_to",
                                                   "generated_from_issue")

    us_queryset = userstories_utils.attach_total_points(us_queryset)
    us_queryset = userstories_utils.attach_role_points(us_queryset)
    us_queryset = attach_total_voters_to_queryset(us_queryset)
    us_queryset = attach_watchers_to_queryset(us_queryset)
    us_queryset = attach_total_watchers_to_queryset(us_queryset)
    us_queryset = attach_is_voter_to_queryset(us_queryset, user)
    us_queryset = attach_is_watcher_to_queryset(us_queryset, user)

    queryset = queryset.prefetch_related(Prefetch("user_stories", queryset=us_queryset))
    queryset = attach_total_points(queryset)
    queryset = attach_closed_points(queryset)

    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_voter_to_queryset(queryset, user)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    return queryset
