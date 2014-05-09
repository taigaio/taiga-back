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

import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as tx
from django.db.models.loading import get_model
from django.core.paginator import Paginator

from reversion import get_unique_for_object

from taiga.projects.history.services import take_snapshot


class Command(BaseCommand):
    help = 'Migrate reversion history to new history system.'

    def efficient_queryset_iter(queryset):
        paginator = Paginator(queryset, 20)
        for page_num in paginator.page_range:
            page = paginator.page(page)
            for element in page.object_list:
                yield element

    def iter_object_with_version(self, model_cls):
        qs = model_cls.objects.all()

        for obj in qs:
            revs = get_unique_for_object(obj)
            for rev in revs:
                yield obj, rev

    def handle_generic_model(self, app_name, model):
        model_cls = get_model(app_name, model)

        for obj, rev in self.iter_object_with_version(model_cls):
            msg = "Processing app:{0} model:{1} pk:{2} revid:{3}."
            print(msg.format(app_name, model.lower(), obj.id, rev.id), file=sys.stderr)

            oldobj = rev.object_version.object
            if rev.revision is None:
                continue

            comment = rev.revision.comment
            user = rev.revision.user
            hentry = take_snapshot(oldobj, user=user, comment=comment)

            if hentry is None:
                continue

            hentry.created_at = rev.revision.date_created
            hentry.save()

    def clear_history(self):
        model_cls = get_model("history", "HistoryEntry")
        model_cls.objects.all().delete()

    @tx.atomic
    def handle(self, *args, **options):
        self.clear_history()
        self.handle_generic_model("tasks", "Task")
        self.handle_generic_model("userstories", "UserStory")
        self.handle_generic_model("issues", "Issue")
