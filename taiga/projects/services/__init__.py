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

# This makes all code that import services works and
# is not the baddest practice ;)

from .bulk_update_order import update_projects_order_in_bulk
from .bulk_update_order import bulk_update_severity_order
from .bulk_update_order import bulk_update_priority_order
from .bulk_update_order import bulk_update_issue_type_order
from .bulk_update_order import bulk_update_issue_status_order
from .bulk_update_order import bulk_update_task_status_order
from .bulk_update_order import bulk_update_points_order
from .bulk_update_order import bulk_update_userstory_status_order

from .filters import get_all_tags

from .invitations import send_invitation
from .invitations import find_invited_user

from .logo import get_logo_small_thumbnail_url
from .logo import get_logo_big_thumbnail_url

from .members import create_members_in_bulk
from .members import get_members_from_bulk
from .members import remove_user_from_project, project_has_valid_admins, can_user_leave_project
from .members import get_max_memberships_for_project, get_total_project_memberships
from .members import check_if_project_can_have_more_memberships

from .modules_config import get_modules_config

from .projects import check_if_project_privacity_can_be_changed
from .projects import check_if_project_can_be_created_or_updated
from .projects import check_if_project_can_be_transfered
from .projects import check_if_project_is_out_of_owner_limits
from .projects import orphan_project
from .projects import delete_project

from .stats import get_stats_for_project_issues
from .stats import get_stats_for_project
from .stats import get_member_stats_for_project

from .tags_colors import update_project_tags_colors_handler

from .transfer import request_project_transfer, start_project_transfer
from .transfer import accept_project_transfer, reject_project_transfer
