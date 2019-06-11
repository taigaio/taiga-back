# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from taiga.base.mails import InlineCSSTemplateMail
from taiga.base.mails import mail_builder

from taiga.projects.models import Project, Membership
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.services import get_history_queryset_by_model_instance

from taiga.users.services import get_user_photo_url
from taiga.front.templatetags.functions import resolve as resolve_front_url


class Command(BaseCommand):
    help = 'Send an example of all emails'

    def add_arguments(self, parser):
        parser.add_argument('--locale', '-l',
                            default=None,
                            dest='locale',
                            help='Send emails in an specific language.')
        parser.add_argument('email',
                            help='Email address to send sample emails to.')


    def handle(self, *args, **options):
        locale = options.get('locale')
        email_address = options.get('email')

        # Register email
        context = {"lang": locale,
                    "user": get_user_model().objects.all().order_by("?").first(),
                    "cancel_token": "cancel-token"}

        email = mail_builder.registered_user(email_address, context)
        email.send()

        # Membership invitation
        membership = Membership.objects.order_by("?").filter(user__isnull=True).first()
        membership.invited_by = get_user_model().objects.all().order_by("?").first()
        membership.invitation_extra_text = "Text example, Text example,\nText example,\n\nText example"

        context = {"lang": locale, "membership": membership}
        email = mail_builder.membership_invitation(email_address, context)
        email.send()

        # Membership notification
        context = {"lang": locale,
                   "membership": Membership.objects.order_by("?").filter(user__isnull=False).first()}
        email = mail_builder.membership_notification(email_address, context)
        email.send()

        # Feedback
        context = {
            "lang": locale,
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
        email = mail_builder.feedback_notification(email_address, context)
        email.send()

        # Password recovery
        context = {"lang": locale, "user": get_user_model().objects.all().order_by("?").first()}
        email = mail_builder.password_recovery(email_address, context)
        email.send()

        # Change email
        context = {"lang": locale, "user": get_user_model().objects.all().order_by("?").first()}
        email = mail_builder.change_email(email_address, context)
        email.send()

        # Export/Import emails
        context = {
            "lang": locale,
            "user": get_user_model().objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
            "error_subject": "Error generating project dump",
            "error_message": "Error generating project dump",
        }
        email = mail_builder.export_error(email_address, context)
        email.send()
        context = {
            "lang": locale,
            "user": get_user_model().objects.all().order_by("?").first(),
            "error_subject": "Error importing project dump",
            "error_message": "Error importing project dump",
        }
        email = mail_builder.import_error(email_address, context)
        email.send()

        deletion_date = timezone.now() + datetime.timedelta(seconds=60*60*24)
        context = {
            "lang": locale,
            "url": "http://dummyurl.com",
            "user": get_user_model().objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
            "deletion_date": deletion_date,
        }
        email = mail_builder.dump_project(email_address, context)
        email.send()

        context = {
            "lang": locale,
            "user": get_user_model().objects.all().order_by("?").first(),
            "project": Project.objects.all().order_by("?").first(),
        }
        email = mail_builder.load_dump(email_address, context)
        email.send()

        # Notification emails
        notification_emails = [
            ("issues.Issue", "issues/issue-change"),
            ("issues.Issue", "issues/issue-create"),
            ("issues.Issue", "issues/issue-delete"),
            ("tasks.Task", "tasks/task-change"),
            ("tasks.Task", "tasks/task-create"),
            ("tasks.Task", "tasks/task-delete"),
            ("userstories.UserStory", "userstories/userstory-change"),
            ("userstories.UserStory", "userstories/userstory-create"),
            ("userstories.UserStory", "userstories/userstory-delete"),
            ("milestones.Milestone", "milestones/milestone-change"),
            ("milestones.Milestone", "milestones/milestone-create"),
            ("milestones.Milestone", "milestones/milestone-delete"),
            ("wiki.WikiPage", "wiki/wikipage-change"),
            ("wiki.WikiPage", "wiki/wikipage-create"),
            ("wiki.WikiPage", "wiki/wikipage-delete"),
        ]

        context = {
            "lang": locale,
            "project": Project.objects.all().order_by("?").first(),
            "changer": get_user_model().objects.all().order_by("?").first(),
            "history_entries": HistoryEntry.objects.all().order_by("?")[0:5],
            "user": get_user_model().objects.all().order_by("?").first(),
        }

        for notification_email in notification_emails:
            model = apps.get_model(*notification_email[0].split("."))
            snapshot = {
                "subject": "Tests subject",
                "ref": 123123,
                "name": "Tests name",
                "slug": "test-slug"
            }
            queryset = model.objects.all().order_by("?")
            for obj in queryset:
                end = False
                entries = get_history_queryset_by_model_instance(obj).filter(is_snapshot=True).order_by("?")

                for entry in entries:
                    if entry.snapshot:
                        snapshot = entry.snapshot
                        end = True
                        break
                if end:
                    break
            context["snapshot"] = snapshot

            cls = type("InlineCSSTemplateMail", (InlineCSSTemplateMail,), {"name": notification_email[1]})
            email = cls()
            email.send(email_address, context)

        # Transfer Emails
        context = {
            "project": Project.objects.all().order_by("?").first(),
            "requester": get_user_model().objects.all().order_by("?").first(),
        }
        email = mail_builder.transfer_request(email_address, context)
        email.send()

        context = {
            "project": Project.objects.all().order_by("?").first(),
            "receiver": get_user_model().objects.all().order_by("?").first(),
            "token": "test-token",
            "reason": "Test reason"
        }
        email = mail_builder.transfer_start(email_address, context)
        email.send()

        context = {
            "project": Project.objects.all().order_by("?").first(),
            "old_owner": get_user_model().objects.all().order_by("?").first(),
            "new_owner": get_user_model().objects.all().order_by("?").first(),
            "reason": "Test reason"
        }
        email = mail_builder.transfer_accept(email_address, context)
        email.send()

        context = {
            "project": Project.objects.all().order_by("?").first(),
            "rejecter": get_user_model().objects.all().order_by("?").first(),
            "reason": "Test reason"
        }
        email = mail_builder.transfer_reject(email_address, context)
        email.send()


        # Contact with project admins email
        project = Project.objects.all().order_by("?").first()
        user = get_user_model().objects.all().order_by("?").first()
        context = {
            "full_name": user.get_full_name(),
            "project_name": project.name,
            "photo_url": get_user_photo_url(user),
            "user_profile_url": resolve_front_url("user", user.username),
            "project_settings_url": resolve_front_url("project-admin", project.slug),
            "comment": "Test comment notification."
        }
        email = mail_builder.contact_notification(email_address, context)
        email.send()

        # GitHub importer email
        context = {
            "project": Project.objects.all().order_by("?").first(),
            "user": get_user_model().objects.all().order_by("?").first()
        }
        email = mail_builder.github_import_success(email_address, context)
        email.send()

        # Jira importer email
        context = {
            "project": Project.objects.all().order_by("?").first(),
            "user": get_user_model().objects.all().order_by("?").first()
        }
        email = mail_builder.jira_import_success(email_address, context)
        email.send()

        # Trello importer email
        context = {
            "project": Project.objects.all().order_by("?").first(),
            "user": get_user_model().objects.all().order_by("?").first()
        }
        email = mail_builder.trello_import_success(email_address, context)
        email.send()

        # Asana importer email
        context = {
            "project": Project.objects.all().order_by("?").first(),
            "user": get_user_model().objects.all().order_by("?").first()
        }
        email = mail_builder.asana_import_success(email_address, context)
        email.send()

        # Error importer email
        context = {
            "user": get_user_model().objects.all().order_by("?").first(),
            "error_subject": "Error importing GitHub project",
            "error_message": "Error importing GitHub project",
            "project": 1234,
            "exception": "Exception message"
        }
        email = mail_builder.importer_import_error(email_address, context)
        email.send()
