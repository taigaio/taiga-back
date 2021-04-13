# -*- coding: utf-8 -*-
import uuid

from django.urls import reverse
from django.conf import settings

from taiga.base.utils.urls import get_absolute_url


# Set this in settings.PROJECT_MODULES_CONFIGURATORS["gitlab"]
def get_or_generate_config(project):
    # Default config
    config = {
        "secret": uuid.uuid4().hex,
        "valid_origin_ips": settings.GITLAB_VALID_ORIGIN_IPS,
    }

    close_status = project.issue_statuses.filter(is_closed=True).order_by("order").first()
    if close_status:
        config["close_status"] = close_status.id

    # Update with current config if exist
    if project.modules_config.config:
        config.update(project.modules_config.config.get("gitlab", {}))

    # Generate webhook url
    url = reverse("gitlab-hook-list")
    url = get_absolute_url(url)
    url = "{}?project={}&key={}".format(url, project.id, config["secret"])
    config["webhooks_url"] = url

    return config
