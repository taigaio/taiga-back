# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

from django.db.models import signals
from django.dispatch import receiver

from . import middleware as mw
from . import changes


@receiver(signals.post_save, dispatch_uid="events_dispatcher_on_change")
def on_save_any_model(sender, instance, created, **kwargs):
    # Ignore any object that can not have project_id
    content_type = changes._get_type_for_model(instance)

    # Ignore any other changes
    if content_type not in changes.watched_types:
        return

    sesionid = mw.get_current_session_id()

    if created:
        changes.emit_change_event_for_model(instance, sesionid, type="create")
    else:
        changes.emit_change_event_for_model(instance, sesionid, type="change")


@receiver(signals.post_delete, dispatch_uid="events_dispatcher_on_delete")
def on_delete_any_model(sender, instance, **kwargs):
    # Ignore any object that can not have project_id
    content_type = changes._get_type_for_model(instance)

    # Ignore any other changes
    if content_type not in changes.watched_types:
        return

    sesionid = mw.get_current_session_id()
    changes.emit_change_event_for_model(instance, sesionid, type="delete")
