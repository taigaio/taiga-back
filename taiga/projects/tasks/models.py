# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from taiga.base.utils.slug import ref_uniquely
from taiga.base.notifications.models import WatchedMixin
from taiga.projects.userstories.models import UserStory
from taiga.projects.milestones.models import Milestone

import reversion


class Task(WatchedMixin):
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
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    finished_date = models.DateTimeField(null=True, blank=True,
                                         verbose_name=_("finished date"))
    subject = models.CharField(max_length=500, null=False, blank=False,
                               verbose_name=_("subject"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                    default=None, related_name="user_storys_assigned_to_me",
                                    verbose_name=_("assigned to"))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                related_name="watched_tasks", verbose_name=_("watchers"))
    tags = PickledObjectField(null=False, blank=True, verbose_name=_("tags"))
    attachments = generic.GenericRelation("projects.Attachment")
    is_iocaine = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is iocaine"))

    notifiable_fields = [
        "subject",
        "owner",
        "assigned_to",
        "finished_date",
        "is_iocaine",
        "status",
        "description",
        "tags",
    ]

    class Meta:
        verbose_name = "task"
        verbose_name_plural = "tasks"
        ordering = ["project", "created_date"]
        unique_together = ("ref", "project")
        permissions = (
            ("view_task", "Can view task"),
        )

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

    def _get_watchers_by_role(self):
        return {
            "owner": self.owner,
            "assigned_to": self.assigned_to,
            "suscribed_watchers": self.watchers.all(),
            "project_owner": (self.project, self.project.owner),
        }


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Task)


# Model related signals handlers
@receiver(models.signals.pre_save, sender=Task, dispatch_uid="task_ref_handler")
def task_ref_handler(sender, instance, **kwargs):
    """
    Automatically assignes a seguent reference code to a
    user story if that is not created.
    """
    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, "last_task_ref", instance.__class__)

def us_has_open_tasks(us, exclude_task):
    qs = us.tasks.all()
    if exclude_task.pk:
        qs = qs.exclude(pk=exclude_task.pk)

    return not all(task.status.is_closed for task in qs)

def milestone_has_open_userstories(milestone):
    qs = milestone.user_stories.exclude(is_closed=True)
    return qs.exists()

@receiver(models.signals.post_delete, sender=Task, dispatch_uid="tasks_close_handler_on_delete")
def tasks_close_handler_on_delete(sender, instance, **kwargs):
    if instance.user_story_id and UserStory.objects.filter(id=instance.user_story_id) and not us_has_open_tasks(us=instance.user_story, exclude_task=instance):
        instance.user_story.is_closed = True
        instance.user_story.finish_date = timezone.now()
        instance.user_story.save(update_fields=["is_closed", "finish_date"])

    if instance.milestone_id and Milestone.objects.filter(id=instance.milestone_id):
        if not milestone_has_open_userstories(instance.milestone):
            instance.milestone.closed = True
            instance.milestone.save(update_fields=["closed"])

@receiver(models.signals.pre_save, sender=Task, dispatch_uid="tasks_close_handler")
def tasks_close_handler(sender, instance, **kwargs):
    if instance.id:
        orig_instance = sender.objects.get(id=instance.id)
    else:
        orig_instance = instance

    if orig_instance.status.is_closed != instance.status.is_closed:
        if orig_instance.status.is_closed and not instance.status.is_closed:
            instance.finished_date = None
            if instance.user_story_id:
                instance.user_story.is_closed = False
                instance.user_story.finish_date = None
                instance.user_story.save(update_fields=["is_closed", "finish_date"])
        else:
            instance.finished_date = timezone.now()
            if instance.user_story_id and not us_has_open_tasks(us=instance.user_story,
                                                                exclude_task=instance):
                instance.user_story.is_closed = True
                instance.user_story.finish_date = timezone.now()
                instance.user_story.save(update_fields=["is_closed", "finish_date"])
    elif not instance.id:
        if not orig_instance.status.is_closed:
            instance.finished_date = None
            if instance.user_story_id:
                instance.user_story.is_closed = False
                instance.user_story.finish_date = None
                instance.user_story.save(update_fields=["is_closed", "finish_date"])
        else:
            instance.finished_date = timezone.now()
            if instance.user_story_id and not us_has_open_tasks(us=instance.user_story,
                                                                exclude_task=instance):
                instance.user_story.is_closed = True
                instance.user_story.finish_date = timezone.now()
                instance.user_story.save(update_fields=["is_closed", "finish_date"])

    # If the task change its US
    if instance.user_story_id != orig_instance.user_story_id:
        if (orig_instance.user_story_id and not orig_instance.status.is_closed
                and not us_has_open_tasks(us=orig_instance.user_story, exclude_task=orig_instance)):
            orig_instance.user_story.is_closed = True
            orig_instance.user_story.finish_date = timezone.now()
            orig_instance.user_story.save(update_fields=["is_closed", "finish_date"])

        if instance.user_story_id:
            if instance.user_story.is_closed:
                if instance.status.is_closed:
                    instance.user_story.finish_date = timezone.now()
                    instance.user_story.save(update_fields=["finish_date"])
                else:
                    instance.user_story.is_closed = False
                    instance.user_story.finish_date = None
                    instance.user_story.save(update_fields=["is_closed", "finish_date"])

    if instance.milestone_id:
        if instance.status.is_closed and not instance.milestone.closed:
            if not milestone_has_open_userstories(instance.milestone):
                instance.milestone.closed = True
                instance.milestone.save(update_fields=["closed"])
        elif not instance.status.is_closed and instance.milestone.closed:
            instance.milestone.closed = False
            instance.milestone.save(update_fields=["closed"])
