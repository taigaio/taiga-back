# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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


from django.core.management.base import BaseCommand

from taiga.base.utils.iterators import iter_queryset
from taiga.projects.notifications.models import HistoryChangeNotification
from taiga.projects.notifications.services import send_sync_notifications

class Command(BaseCommand):

    def handle(self, *args, **options):
        qs = HistoryChangeNotification.objects.all()
        for change_notification in iter_queryset(qs, itersize=100):
            send_sync_notifications(change_notification.pk)
