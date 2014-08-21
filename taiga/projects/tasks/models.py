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

from django.db import models
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from taiga.base.tags import TaggedMixin
from taiga.base.utils.slug import ref_uniquely
from taiga.projects.notifications import WatchedModelMixin
from taiga.projects.occ import OCCModelMixin
from taiga.projects.userstories.models import UserStory
from taiga.projects.userstories import services as us_service
from taiga.projects.milestones.models import Milestone
from taiga.projects.mixins.blocked import BlockedMixin
from taiga.projects.services.tags_colors import update_project_tags_colors_handler, remove_unused_tags


class Task(OCCModelMixin, WatchedModelMixin, BlockedMixin, TaggedMixin, models.Model):
    user_story = models.ForeignKey("userstories.UserStory", null=True, blank=True,
                                   related_name="tasks", verbose_name=_("user story"))
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                              related_name="owned_tasks", verbose_name=_("owner"))
    status = models.ForeignKey("projects.TaskStatus", null=False, blank=False,
                               related_name="tasks", verbose_name=_("status"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="tasks", verbose_name=_("project"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True,
                                  default=None, related_name="tasks",
                                  verbose_name=_("milestone"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    finished_date = models.DateTimeField(null=True, blank=True,
                                         verbose_name=_("finished date"))
    subject = models.TextField(null=False, blank=False,
                               verbose_name=_("subject"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                    default=None, related_name="tasks_assigned_to_me",
                                    verbose_name=_("assigned to"))
    attachments = generic.GenericRelation("attachments.Attachment")
    is_iocaine = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is iocaine"))
    _importing = None

    class Meta:
        verbose_name = "task"
        verbose_name_plural = "tasks"
        ordering = ["project", "created_date"]
        # unique_together = ("ref", "project")
        permissions = (
            ("view_task", "Can view task"),
        )

    def save(self, *args, **kwargs):
        if not self._importing:
            self.modified_date = timezone.now()

        return super().save(*args, **kwargs)

    def __str__(self):
        return "({1}) {0}".format(self.ref, self.subject)

    def get_notifiable_assigned_to_display(self, value):
        if not value:
            return _("Unassigned")
        return value.get_full_name()

    def get_notifiable_tags_display(self, value):
        if type(value) is list:
            return ", ".join(value)
        return value


def milestone_has_open_userstories(milestone):
    qs = milestone.user_stories.exclude(is_closed=True)
    return qs.exists()


@receiver(models.signals.post_delete, sender=Task, dispatch_uid="tasks_milestone_close_handler_on_delete")
def tasks_milestone_close_handler_on_delete(sender, instance, **kwargs):
    if instance.milestone_id and Milestone.objects.filter(id=instance.milestone_id):
        if not milestone_has_open_userstories(instance.milestone):
            instance.milestone.closed = True
            instance.milestone.save(update_fields=["closed"])


# Define the previous version of the task for use it on the post_save handler
@receiver(models.signals.pre_save, sender=Task, dispatch_uid="tasks_us_close_handler")
def tasks_us_close_handler(sender, instance, **kwargs):
    instance.prev = None
    if instance.id:
        instance.prev = sender.objects.get(id=instance.id)


@receiver(models.signals.post_save, sender=Task, dispatch_uid="tasks_us_close_on_create_handler")
def tasks_us_close_on_create_handler(sender, instance, created, **kwargs):
    if instance.user_story_id:
        if us_service.calculate_userstory_is_closed(instance.user_story):
            us_service.close_userstory(instance.user_story)
        else:
            us_service.open_userstory(instance.user_story)

    if instance.prev and instance.prev.user_story_id:
        if us_service.calculate_userstory_is_closed(instance.prev.user_story):
            us_service.close_userstory(instance.prev.user_story)
        else:
            us_service.open_userstory(instance.prev.user_story)


@receiver(models.signals.post_delete, sender=Task, dispatch_uid="tasks_us_close_handler_on_delete")
def tasks_us_close_handler_on_delete(sender, instance, **kwargs):
    if instance.user_story_id:
        if us_service.calculate_userstory_is_closed(instance.user_story):
            us_service.close_userstory(instance.user_story)
        else:
            us_service.open_userstory(instance.user_story)


@receiver(models.signals.pre_save, sender=Task, dispatch_uid="tasks_milestone_close_handler")
def tasks_milestone_close_handler(sender, instance, **kwargs):
    if instance.milestone_id:
        if instance.status.is_closed and not instance.milestone.closed:
            if not milestone_has_open_userstories(instance.milestone):
                instance.milestone.closed = True
                instance.milestone.save(update_fields=["closed"])
        elif not instance.status.is_closed and instance.milestone.closed:
            instance.milestone.closed = False
            instance.milestone.save(update_fields=["closed"])


@receiver(models.signals.post_save, sender=Task, dispatch_uid="task_update_project_colors")
def task_update_project_tags(sender, instance, **kwargs):
    update_project_tags_colors_handler(instance)


@receiver(models.signals.post_delete, sender=Task, dispatch_uid="task_update_project_colors_on_delete")
def task_update_project_tags_on_delete(sender, instance, **kwargs):
    remove_unused_tags(instance.project)
    instance.project.save()
