# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import logging
import sys

from django.utils.translation import gettext as _

from taiga.base.mails import mail_builder
from taiga.users.models import User
from taiga.celery import app
from .normal import JiraNormalImporter
from .agile import JiraAgileImporter

logger = logging.getLogger('taiga.importers.jira')


@app.task(bind=True)
def import_project(self, user_id, url, token, project_id, options, importer_type):
    user = User.objects.get(id=user_id)

    if importer_type == "agile":
        importer = JiraAgileImporter(user, url, token)
    else:
        importer = JiraNormalImporter(user, url, token)

    try:
        project = importer.import_project(project_id, options)
    except Exception as e:
        # Error
        ctx = {
            "user": user,
            "error_subject": _("Error importing Jira project"),
            "error_message": _("Error importing Jira project"),
            "project": project_id,
            "exception": e
        }
        email = mail_builder.importer_import_error(user, ctx)
        email.send()
        logger.error('Error importing Jira project %s (by %s)', project_id, user, exc_info=sys.exc_info())
    else:
        ctx = {
            "project": project,
            "user": user,
        }
        email = mail_builder.jira_import_success(user, ctx)
        email.send()
