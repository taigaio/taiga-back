# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

def handle_move_on_destroy_issue_status(sender, deleted, moved, **kwargs):
    if not hasattr(deleted.project, "modules_config"):
        return

    modules_config = deleted.project.modules_config

    if modules_config.config and modules_config.config.get("github", {}):
        current_status_id = modules_config.config.get("github", {}).get("close_status", None)

        if current_status_id and current_status_id == deleted.id:
            modules_config.config["github"]["close_status"] = moved.id
            modules_config.save()
