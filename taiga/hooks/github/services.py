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
