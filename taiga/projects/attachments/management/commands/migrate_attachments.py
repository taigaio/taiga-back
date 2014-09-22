import re

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings
from django.db import transaction

from taiga.base.utils.iterators import iter_queryset

url = """
https://api-taiga.kaleidos.net/attachments/446/?user=8&amp;token=9ac0fc593e9c07740975c6282e1e501189578faa
"""

class Command(BaseCommand):
    help = "Parses all objects and try replace old attachments url with one new"


    trx = r"((?:https?)://api-taiga\.kaleidos\.net/attachments/(\d+)/[^\s\"]+)"

    @transaction.atomic
    def handle(self, *args, **options):
        settings.MEDIA_URL="https://media.taiga.io/"

        self.move_user_photo()
        self.move_attachments()
        self.process_userstories()
        self.process_issues()
        self.process_wiki()
        self.process_tasks()
        self.process_history()

    def move_attachments(self):
        print("Moving all attachments to new location")

        Attachment = apps.get_model("attachments", "Attachment")
        qs = Attachment.objects.all()

        for item in iter_queryset(qs):
            try:
                with transaction.atomic():
                    old_file = item.attached_file
                    item.attached_file = File(old_file)
                    item.save()
            except FileNotFoundError:
                item.delete()

    def move_user_photo(self):
        print("Moving all user photos to new location")

        User = apps.get_model("users", "User")
        qs = User.objects.all()

        for item in iter_queryset(qs):
            try:
                with transaction.atomic():
                    old_file = item.photo
                    item.photo = File(old_file)
                    item.save()
            except FileNotFoundError:
                pass

    def get_attachment_real_url(self, pk):
        if isinstance(pk, str):
            pk = int(pk)

        Attachment = apps.get_model("attachments", "Attachment")
        return Attachment.objects.get(pk=pk).attached_file.url

    def replace_matches(self, data):
        matches = re.findall(self.trx, data)

        original_data = data

        if len(matches) == 0:
            return data

        for url, attachment_id in matches:
            new_url = self.get_attachment_real_url(attachment_id)
            print("Match {} replaced by {}".format(url, new_url))

            try:
                data = data.replace(url, self.get_attachment_real_url(attachment_id))
            except Exception as e:
                print("Exception found but ignoring:", e)

            assert data != original_data

        return data

    def process_userstories(self):
        UserStory = apps.get_model("userstories", "UserStory")
        qs = UserStory.objects.all()

        for item in iter_queryset(qs):
            description = self.replace_matches(item.description)
            UserStory.objects.filter(pk=item.pk).update(description=description)

    def process_tasks(self):
        Task = apps.get_model("tasks", "Task")
        qs = Task.objects.all()

        for item in iter_queryset(qs):
            description = self.replace_matches(item.description)
            Task.objects.filter(pk=item.pk).update(description=description)

    def process_issues(self):
        Issue = apps.get_model("issues", "Issue")
        qs = Issue.objects.all()

        for item in iter_queryset(qs):
            description = self.replace_matches(item.description)
            Issue.objects.filter(pk=item.pk).update(description=description)

    def process_wiki(self):
        WikiPage = apps.get_model("wiki", "WikiPage")
        qs = WikiPage.objects.all()

        for item in iter_queryset(qs):
            content = self.replace_matches(item.content)
            WikiPage.objects.filter(pk=item.pk).update(content=content)

    def process_history(self):
        HistoryEntry = apps.get_model("history", "HistoryEntry")
        qs = HistoryEntry.objects.all()

        for item in iter_queryset(qs):
            comment = self.replace_matches(item.comment)
            comment_html = self.replace_matches(item.comment_html)
            HistoryEntry.objects.filter(pk=item.pk).update(comment=comment, comment_html=comment_html)
