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

import datetime
import logging
import sys
import gzip

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone

from django.conf import settings
from django.utils.translation import ugettext as _

from taiga.base.mails import mail_builder
from taiga.base.utils import json
from taiga.celery import app

from . import exceptions as err
from . import services
from .renderers import ExportRenderer

logger = logging.getLogger('taiga.export_import')

import resource


@app.task(bind=True)
def dump_project(self, user, project, dump_format):
    try:
        if dump_format == "gzip":
            path = "exports/{}/{}-{}.json.gz".format(project.pk, project.slug, self.request.id)
            storage_path = default_storage.path(path)
            with default_storage.open(storage_path, mode="wb") as outfile:
                services.render_project(project, gzip.GzipFile(fileobj=outfile))
        else:
            path = "exports/{}/{}-{}.json".format(project.pk, project.slug, self.request.id)
            storage_path = default_storage.path(path)
            with default_storage.open(storage_path, mode="wb") as outfile:
                services.render_project(project, outfile)

        url = default_storage.url(path)

    except Exception:
        # Error
        ctx = {
            "user": user,
            "error_subject": _("Error generating project dump"),
            "error_message": _("Error generating project dump"),
            "project": project
        }
        email = mail_builder.export_error(user, ctx)
        email.send()
        logger.error('Error generating dump %s (by %s)', project.slug, user, exc_info=sys.exc_info())
    else:
        # Success
        deletion_date = timezone.now() + datetime.timedelta(seconds=settings.EXPORTS_TTL)
        ctx = {
            "url": url,
            "project": project,
            "user": user,
            "deletion_date": deletion_date
        }
        email = mail_builder.dump_project(user, ctx)
        email.send()


@app.task
def delete_project_dump(project_id, project_slug, task_id, dump_format):
    if dump_format == "gzip":
        path = "exports/{}/{}-{}.json.gz".format(project_id, project_slug, task_id)
    else:
        path = "exports/{}/{}-{}.json".format(project_id, project_slug, task_id)
    default_storage.delete(path)


ADMIN_ERROR_LOAD_PROJECT_DUMP_MESSAGE = _("""

Error loading dump by {user_full_name} <{user_email}>:"


REASON:
-------
{reason}

DETAILS:
--------
{details}

TRACE ERROR:
------------""")


@app.task
def load_project_dump(user, dump):
    try:
        project = services.store_project_from_dict(dump, user)
    except err.TaigaImportError as e:
        # On Error
        ## remove project
        if e.project:
            e.project.delete_related_content()
            e.project.delete()

        ## send email to the user
        error_subject = _("Error loading project dump")
        error_message = e.message or _("Error loading your project dump file")

        ctx = {
            "user": user,
            "error_subject": error_message,
            "error_message": error_subject,
        }
        email = mail_builder.import_error(user, ctx)
        email.send()

        ## logged the error to sysadmins
        text = ADMIN_ERROR_LOAD_PROJECT_DUMP_MESSAGE.format(
            user_full_name=user,
            user_email=user.email,
            reason=e.message or _("  -- no detail info --"),
            details=json.dumps(e.errors, indent=4)
        )
        logger.error(text, exc_info=sys.exc_info())

    else:
        # On Success
        ctx = {"user": user, "project": project}
        email = mail_builder.load_dump(user, ctx)
        email.send()
