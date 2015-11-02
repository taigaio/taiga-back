# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from django.conf import settings
from django.utils import timezone

from taiga.projects.history import services as history_service
from taiga.projects.history.choices import HistoryType

from . import tasks


def _get_project_webhooks(project):
    webhooks = []
    for webhook in project.webhooks.all():
        webhooks.append({
            "id": webhook.pk,
            "url": webhook.url,
            "key": webhook.key,
        })
    return webhooks


def on_new_history_entry(sender, instance, created, **kwargs):
    if not settings.WEBHOOKS_ENABLED:
        return None

    if instance.is_hidden:
        return None

    model = history_service.get_model_from_key(instance.key)
    pk = history_service.get_pk_from_key(instance.key)
    obj = model.objects.get(pk=pk)

    webhooks = _get_project_webhooks(obj.project)

    if instance.type == HistoryType.create:
        task = tasks.create_webhook
        extra_args = []
    elif instance.type == HistoryType.change:
        task = tasks.change_webhook
        extra_args = [instance]
    elif instance.type == HistoryType.delete:
        task = tasks.delete_webhook
        extra_args = [timezone.now()]

    for webhook in webhooks:
        args = [webhook["id"], webhook["url"], webhook["key"], obj] + extra_args

        if settings.CELERY_ENABLED:
            task.delay(*args)
        else:
            task(*args)
