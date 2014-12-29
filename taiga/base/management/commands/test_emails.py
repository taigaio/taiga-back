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

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from djmail.template_mail import MagicMailBuilder, InlineCSSTemplateMail

from taiga.projects.models import Project, Membership
from taiga.projects.history.models import HistoryEntry
from taiga.users.models import User


class Command(BaseCommand):
    args = '<email>'
    help = 'Send an example of all emails'

    def handle(self, *args, **options):
        if len(args) != 1:
            print("Usage: ./manage.py test_emails <email-address>")
            return

        test_email = args[0]

        mbuilder = MagicMailBuilder(template_mail_cls=InlineCSSTemplateMail)

        # Register email
        context = {"user": User.objects.all().order_by("?").first(), "cancel_token": "cancel-token"}
        email = mbuilder.registered_user(test_email, context)
        email.send()

        # Membership invitation
        context = {"membership": Membership.objects.order_by("?").filter(user__isnull=True).first()}
        email = mbuilder.membership_invitation(test_email, context)
        email.send()

        # Membership notification
        context = {"membership": Membership.objects.order_by("?").filter(user__isnull=False).first()}
        email = mbuilder.membership_notification(test_email, context)
        email.send()

        # Feedback
        context = {
            "feedback_entry": {
                "full_name": "Test full name",
                "email": "test@email.com",
                "comment": "Test comment",
            },
            "extra": {
                "key1": "value1",
                "key2": "value2",
            },
        }
        email = mbuilder.feedback_notification(test_email, context)
        email.send()

        # Password recovery
        context = {"user": User.objects.all().order_by("?").first()}
        email = mbuilder.password_recovery(test_email, context)
        email.send()

        # Change email
        context = {"user": User.objects.all().order_by("?").first()}
        email = mbuilder.change_email(test_email, context)
        email.send()

        # Export/Import emails
        context = {
            "user": User.objects.all().order_by("?").first(),
            "error_subject": "Error generating project dump",
            "error_message": "Error generating project dump",
        }
        email = mbuilder.export_import_error(test_email, context)
        email.send()

        deletion_date = timezone.now() + datetime.timedelta(seconds=60*60*24)
        context = {
            "url": "http://dummyurl.com",
            "user": User.objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
            "deletion_date": deletion_date,
        }
        email = mbuilder.dump_project(test_email, context)
        email.send()

        context = {
            "user": User.objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
        }
        email = mbuilder.load_dump(test_email, context)
        email.send()

        # Notification emails
        notification_emails = [
            "issues/issue-change",
            "issues/issue-create",
            "issues/issue-delete",
            "milestones/milestone-change",
            "milestones/milestone-create",
            "milestones/milestone-delete",
            "projects/project-change",
            "projects/project-create",
            "projects/project-delete",
            "tasks/task-change",
            "tasks/task-create",
            "tasks/task-delete",
            "userstories/userstory-change",
            "userstories/userstory-create",
            "userstories/userstory-delete",
            "wiki/wikipage-change",
            "wiki/wikipage-create",
            "wiki/wikipage-delete",
        ]

        context = {
           "snapshot": HistoryEntry.objects.filter(is_snapshot=True).order_by("?")[0].snapshot,
           "project": Project.objects.all().order_by("?").first(),
           "changer": User.objects.all().order_by("?").first(),
           "history_entries": HistoryEntry.objects.all().order_by("?")[0:5],
           "user": User.objects.all().order_by("?").first(),
        }

        for notification_email in notification_emails:
            cls = type("InlineCSSTemplateMail", (InlineCSSTemplateMail,), {"name": notification_email})
            email = cls()
            email.send(test_email, context)
