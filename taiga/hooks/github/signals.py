# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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


def handle_move_on_destroy_issue_status(sender, deleted, moved, **kwargs):
    if not hasattr(deleted.project, "modules_config"):
        return

    modules_config = deleted.project.modules_config

    if modules_config.config and modules_config.config.get("github", {}):
        current_status_id = modules_config.config.get("github", {}).get("close_status", None)

        if current_status_id and current_status_id == deleted.id:
            modules_config.config["github"]["close_status"] = moved.id
            modules_config.save()
