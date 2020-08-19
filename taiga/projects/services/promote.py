# Copyright (C) 2014-2019 Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from taiga.projects.attachments.models import Attachment
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.services import (get_history_queryset_by_model_instance,
                                             make_key_from_model_object)
from taiga.projects.issues.models import Issue
from taiga.projects.notifications.models import Watched
from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.votes.models import Vote, Votes


def promote_to_us(source_obj):
    model_class = source_obj.__class__
    queryset = model_class.objects.filter(pk=source_obj.id)
    queryset = queryset.prefetch_related("attachments")
    queryset = queryset.select_related("owner",
                                       "assigned_to",
                                       "project")
    queryset = attach_watchers_to_queryset(queryset)

    us_refs = []
    for obj in queryset:
        us = UserStory.objects.create(
            generated_from_issue_id=obj.id if isinstance(source_obj, Issue) else None,
            from_task_ref = _("Task #%(ref)s") % {"ref": obj.ref} if isinstance(source_obj, Task) else None,
            project=obj.project,
            owner=obj.owner,
            subject=obj.subject,
            description=obj.description,
            tags=obj.tags,
            milestone=obj.milestone,
        )

        content_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(us)

        # add data only for task conversion
        if isinstance(source_obj, Task):
            us.due_date = obj.due_date
            us.due_date_reason = obj.due_date_reason
            us.is_blocked = obj.is_blocked
            us.blocked_note = obj.blocked_note
            us.save()

            _import_votes(obj, us)

        _import_assigned(obj, us)
        _import_comments(obj, us)
        _import_attachments(obj, us, content_type)
        _import_watchers(obj, us, content_type)

        us_refs.append(us.ref)

    return us_refs


def _import_assigned(source_obj, target_obj):
    if source_obj.assigned_to:
        target_obj.assigned_users.add(source_obj.assigned_to)


def _import_comments(source_obj, target_obj):
    pre_save = signals.pre_save.receivers
    post_save = signals.post_save.receivers
    signals.pre_save.receivers = []
    signals.post_save.receivers = []

    comments = (
        get_history_queryset_by_model_instance(source_obj)
            .exclude(comment__exact='')
    )
    us_key = make_key_from_model_object(target_obj)

    for entry in comments.all():
        HistoryEntry.objects.create(
            user=entry.user,
            project_id=entry.project_id,
            key=us_key,
            type=entry.type,
            snapshot=None,
            diff=entry.diff,
            values=entry.values,
            comment=entry.comment,
            comment_html=entry.comment_html,
            delete_comment_date=entry.delete_comment_date,
            delete_comment_user=entry.delete_comment_user,
            is_hidden=False,
            is_snapshot=False,
            created_at=entry.created_at
        )

    signals.pre_save.receivers = pre_save
    signals.post_save.receivers = post_save


def _import_watchers(source_obj, target_obj, content_type):

    for watcher_id in source_obj.watchers:
        Watched.objects.create(
            content_type=content_type,
            object_id=target_obj.id,
            user_id=watcher_id,
            project=source_obj.project)


def _import_attachments(source_obj, target_obj, content_type):
    for attachment in source_obj.attachments.all():
        att = Attachment(
            owner=attachment.owner,
            project=attachment.project,
            content_type=content_type,
            object_id=target_obj.id,
            name=attachment.name,
            size=attachment.size,
            created_date=attachment.created_date,
            is_deprecated=attachment.is_deprecated,
            description=attachment.description,
        )
        attached_file = attachment.attached_file
        att.attached_file.save(attachment.name, ContentFile(attached_file.read()), save=True)


def _import_votes(source_obj, target_obj):
    source_content_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(source_obj)
    target_content_type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(target_obj)
    (
        Vote.objects
            .filter(content_type=source_content_type, object_id=source_obj.id)
            .update(content_type=target_content_type, object_id=target_obj.id)
    )

    (
        Votes.objects
            .filter(content_type=source_content_type, object_id=source_obj.id)
            .update(content_type=target_content_type, object_id=target_obj.id)
    )
