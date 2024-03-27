# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# This makes all code that import services works and
# is not the baddest practice ;)

# flake8: noqa


from .bulk_update_order import apply_order_updates
from .bulk_update_order import bulk_update_severity_order
from .bulk_update_order import bulk_update_priority_order
from .bulk_update_order import bulk_update_issue_type_order
from .bulk_update_order import bulk_update_issue_status_order
from .bulk_update_order import bulk_update_task_status_order
from .bulk_update_order import bulk_update_points_order
from .bulk_update_order import bulk_update_userstory_status_order
from .bulk_update_order import bulk_update_epic_status_order
from .bulk_update_order import bulk_update_swimlane_order
from .bulk_update_order import update_projects_order_in_bulk

from .filters import get_all_tags

from .invitations import send_invitation
from .invitations import find_invited_user

from .logo import get_logo_small_thumbnail_url
from .logo import get_logo_big_thumbnail_url

from .members import create_members_in_bulk
from .members import get_members_from_bulk
from .members import remove_user_from_project, project_has_valid_admins, can_user_leave_project
from .members import get_max_memberships_for_project, get_total_project_memberships
from .members import check_if_new_member_can_be_created
from .members import check_if_new_members_can_be_created

from .modules_config import get_modules_config

from .projects import check_if_project_privacy_can_be_changed
from .projects import check_if_project_can_be_created_or_updated
from .projects import check_if_project_can_be_transfered
from .projects import check_if_project_can_be_duplicate
from .projects import check_if_project_is_out_of_owner_limits
from .projects import orphan_project
from .projects import delete_project
from .projects import delete_projects
from .projects import duplicate_project

from .stats import get_stats_for_project_issues
from .stats import get_stats_for_project
from .stats import get_member_stats_for_project

from .transfer import request_project_transfer, start_project_transfer
from .transfer import accept_project_transfer, reject_project_transfer
