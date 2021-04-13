# -*- coding: utf-8 -*-
import uuid

from django.urls import reverse

from taiga.base.utils.urls import get_absolute_url


# Set this in settings.PROJECT_MODULES_CONFIGURATORS["github"]
def get_or_generate_config(project):
    # Default config
    config = {
        "secret": uuid.uuid4().hex
    }

    close_status = project.issue_statuses.filter(is_closed=True).order_by("order").first()
    if close_status:
        config["close_status"] = close_status.id

    # Update with current config if exist
    if project.modules_config.config:
        config.update(project.modules_config.config.get("github", {}))

    # Generate webhook url
    url = reverse("github-hook-list")
    url = get_absolute_url(url)
    url = "%s?project=%s" % (url, project.id)
    config["webhooks_url"] = url
    return config
