import re
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.core.paginator import Paginator
from django.db.models.loading import get_model
from django.db.models import signals
from django.db import models
from django.db import transaction as tx

from reversion import get_unique_for_object

from taiga.projects.references.models import make_reference


class Command(BaseCommand):
    help = "Migrate old references to new references system."

    def iter_queryset(self, queryset):
        paginator = Paginator(queryset, 20)
        for page_num in paginator.page_range:
            page = paginator.page(page_num)
            for element in page.object_list:
                yield element

    def iter_object_versions(self, instance):
        revs = get_unique_for_object(instance)
        for rev in revs:
            yield rev

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refmap = defaultdict(lambda: {"us": {}, "task": {}, "issue": {},})

    @tx.atomic
    def handle(self, *args, **options):
        self.disable_signals()
        self.process_userstories_refs()
        self.process_issues_refs()
        self.process_tasks_refs()

        self.process_userstories_comments()
        self.process_issues_comments()
        self.process_tasks_comments()
        self.process_wikipages()

    def replace_references_on_text(self, ppk, text):
        matches = re.findall(r"(\:((?:us|issue|task))\:(\d+))", text)
        for val, t, ref in matches:
            ref = int(ref)
            if ref not in self.refmap[ppk][t]:
                continue

            newref = self.refmap[ppk][t][ref]
            text = text.replace(val, ":{}:{}".format(t, newref))

        matches =  re.findall(r"(((?:US|Issue|Task)) \#(\d+))", text)
        for val, t, ref in matches:
            ref = int(ref)
            if ref not in self.refmap[ppk][t.lower()]:
                continue

            newref = self.refmap[ppk][t.lower()][ref]
            text = text.replace(val, "{} #{}".format(t, newref))

        return text

    def disable_signals(self):
        print(".. Disabling signals.")
        issue_model = get_model("issues", "Issue")
        us_model = get_model("userstories", "UserStory")
        task_model = get_model("tasks", "Task")
        project_model = get_model("projects", "Project")

        models.signals.post_save.disconnect(dispatch_uid="refus", sender=us_model)
        models.signals.post_save.disconnect(dispatch_uid="refissue", sender=issue_model)
        models.signals.post_save.disconnect(dispatch_uid="reftask", sender=task_model)
        models.signals.post_save.disconnect(dispatch_uid="refproj", sender=project_model)

    def process_userstories_comments(self):
        print(".. Processing userstory comments.")
        model_cls = get_model("userstories", "UserStory")

        for item in self.iter_queryset(model_cls.objects.all()):
            item.description = self.replace_references_on_text(item.project_id, item.description)
            item.blocked_note = self.replace_references_on_text(item.project_id, item.blocked_note)
            item.save()

            for rev in self.iter_object_versions(item):
                rev.revision.comment = self.replace_references_on_text(item.project_id, rev.revision.comment)
                rev.revision.save()
                rev.save()

    def process_issues_comments(self):
        print(".. Processing issues comments.")
        model_cls = get_model("issues", "Issue")

        for item in self.iter_queryset(model_cls.objects.all()):
            item.description = self.replace_references_on_text(item.project_id, item.description)
            item.blocked_note = self.replace_references_on_text(item.project_id, item.blocked_note)
            item.save()

            for rev in self.iter_object_versions(item):
                rev.revision.comment = self.replace_references_on_text(item.project_id, rev.revision.comment)
                rev.revision.save()
                rev.save()

    def process_tasks_comments(self):
        print(".. Processing task comments.")
        model_cls = get_model("tasks", "Task")

        for item in self.iter_queryset(model_cls.objects.all()):
            item.description = self.replace_references_on_text(item.project_id, item.description)
            item.blocked_note = self.replace_references_on_text(item.project_id, item.blocked_note)
            item.save()

            for rev in self.iter_object_versions(item):
                rev.revision.comment = self.replace_references_on_text(item.project_id, rev.revision.comment)
                rev.revision.save()
                rev.save()

    def process_wikipages(self):
        print(".. Processing wikipages.")
        model_cls = get_model("wiki", "WikiPage")

        for item in self.iter_queryset(model_cls.objects.all()):
            item.content = self.replace_references_on_text(item.project_id, item.content)
            item.save()

            for rev in self.iter_object_versions(item):
                rev.revision.comment = self.replace_references_on_text(item.project_id, rev.revision.comment)
                rev.revision.save()
                rev.save()

    def process_userstories_refs(self):
        print(".. Processing userstories.")
        model_cls = get_model("userstories", "UserStory")
        queryset = model_cls.objects.only("ref")

        for item in self.iter_queryset(queryset):
            refval, _ = make_reference(item, item.project, create=True)
            print("process us {0}: {1} -> {2}".format(item.pk, item.ref, refval))
            self.refmap[item.project_id]["us"][item.ref] = refval
            item.ref = refval
            item.save(update_fields=["ref"])

    def process_tasks_refs(self):
        print(".. Processing tasks.")
        model_cls = get_model("tasks", "Task")
        queryset = model_cls.objects.only("ref")

        for item in self.iter_queryset(queryset):
            refval, _ = make_reference(item, item.project, create=True)
            print("process task {0}: {1} -> {2}".format(item.pk, item.ref, refval))
            self.refmap[item.project_id]["task"][item.ref] = refval
            item.ref = refval
            item.save(update_fields=["ref"])

    def process_issues_refs(self):
        print(".. Processing issues.")
        model_cls = get_model("issues", "Issue")
        queryset = model_cls.objects.all()

        for item in self.iter_queryset(queryset):
            refval, _ = make_reference(item, item.project, create=True)
            print("process issue {0}: {1} -> {2}".format(item.pk, item.ref, refval))
            self.refmap[item.project_id]["issue"][item.ref] = refval
            item.ref = refval
            item.save()


