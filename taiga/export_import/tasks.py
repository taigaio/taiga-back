# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone

from django.conf import settings
from django.utils.translation import ugettext as _

from djmail.template_mail import MagicMailBuilder, InlineCSSTemplateMail

from taiga.celery import app

from .service import project_to_dict
from .dump_service import dict_to_project
from .renderers import ExportRenderer

logger = logging.getLogger('taiga.export_import')


@app.task(bind=True)
def dump_project(self, user, project):
    mbuilder = MagicMailBuilder(template_mail_cls=InlineCSSTemplateMail)
    path = "exports/{}/{}-{}.json".format(project.pk, project.slug, self.request.id)

    try:
        content = ExportRenderer().render(project_to_dict(project), renderer_context={"indent": 4})
        content = content.decode('utf-8')
        content = ContentFile(content)

        default_storage.save(path, content)
        url = default_storage.url(path)
    except Exception:
        ctx = {
            "user": user,
            "error_subject": _("Error generating project dump"),
            "error_message": _("Error generating project dump"),
            "project": project
        }
        email = mbuilder.export_error(user, ctx)
        email.send()
        logger.error('Error generating dump %s (by %s)', project.slug, user, exc_info=sys.exc_info())
        return

    deletion_date = timezone.now() + datetime.timedelta(seconds=settings.EXPORTS_TTL)
    ctx = {
        "url": url,
        "project": project,
        "user": user,
        "deletion_date": deletion_date
    }
    email = mbuilder.dump_project(user, ctx)
    email.send()


@app.task
def delete_project_dump(project_id, project_slug, task_id):
    default_storage.delete("exports/{}/{}-{}.json".format(project_id, project_slug, task_id))


@app.task
def load_project_dump(user, dump):
    mbuilder = MagicMailBuilder(template_mail_cls=InlineCSSTemplateMail)

    try:
        project = dict_to_project(dump, user.email)
    except Exception:
        ctx = {
            "user": user,
            "error_subject": _("Error loading project dump"),
            "error_message": _("Error loading project dump"),
        }
        email = mbuilder.import_error(user, ctx)
        email.send()
        logger.error('Error loading dump %s (by %s)', project.slug, user, exc_info=sys.exc_info())
        return

    ctx = {"user": user, "project": project}
    email = mbuilder.load_dump(user, ctx)
    email.send()
