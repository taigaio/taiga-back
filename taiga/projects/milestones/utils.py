# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.db.models import Prefetch

from taiga.projects.userstories import utils as userstories_utils


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
                                                   "owner")

    us_queryset = userstories_utils.attach_total_points(us_queryset)
    us_queryset = userstories_utils.attach_role_points(us_queryset)
    us_queryset = userstories_utils.attach_epics(us_queryset)

    queryset = queryset.prefetch_related(Prefetch("user_stories", queryset=us_queryset))

    queryset = attach_total_points(queryset)
    queryset = attach_closed_points(queryset)

    return queryset
