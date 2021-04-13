# -*- coding: utf-8 -*-
def handle_move_on_destroy_issue_status(sender, deleted, moved, **kwargs):
    if not hasattr(deleted.project, "modules_config"):
        return

    modules_config = deleted.project.modules_config

    if modules_config.config and modules_config.config.get("gitlab", {}):
        current_status_id = modules_config.config.get("gitlab", {}).get("close_status", None)

        if current_status_id and current_status_id == deleted.id:
            modules_config.config["gitlab"]["close_status"] = moved.id
            modules_config.save()
