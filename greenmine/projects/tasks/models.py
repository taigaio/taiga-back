# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from greenmine.base.utils.slug import ref_uniquely
from greenmine.base.notifications.models import WatchedMixin

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


@receiver(models.signals.pre_save, sender=Task, dispatch_uid="tasks_close_handler")
def tasks_close_handler(sender, instance, **kwargs):
    # USs
    if instance.id:                                                             # Edit task
        if (sender.objects.get(id=instance.id).status.is_closed == False and
                instance.status.is_closed == True):                             # Close task
            instance.finished_date = timezone.now()
            if instance.user_story and (all([task.status.is_closed for task in
                    instance.user_story.tasks.exclude(id=instance.id)])):       # All close
                us_closed_status = instance.project.us_statuses.filter(
                                                         is_closed=True).order_by(
                                                                           "order")[0]
                instance.user_story.status = us_closed_status
                instance.user_story.finish_date = timezone.now()
                instance.user_story.save()
        elif (sender.objects.get(id=instance.id).status.is_closed == True and
                instance.status.is_closed == False):                            # Opene task
            instance.finished_date = None
            if instance.user_story and instance.user_story.status.is_closed == True: # Us close
                us_opened_status = instance.project.us_statuses.filter(
                                                        is_closed=False).order_by(
                                                                          "-order")[0]
                instance.user_story.status = us_opened_status
                instance.user_story.finish_date = None
                instance.user_story.save()
    else:                                                                      # Create Task
        if instance.status.is_closed == True:                                # Task is close
            instance.finished_date = timezone.now()
            if instance.user_story:
                if instance.user_story.status.is_closed == True: # Us is close
                    instance.user_story.finish_date = timezone.now()
                    instance.user_story.save()
                elif all([task.status.is_closed for task in
                                                    instance.user_story.tasks.all()]):  # All us's tasks are close
                    # if any stupid robot/machine/user/alien create an open US
                    us_closed_status = instance.project.us_statuses.filter(is_closed=True).order_by("order")[0]
                    instance.user_story.status = us_closed_status
                    instance.user_story.finish_date = timezone.now()
                    instance.user_story.save()
        else:                                                               # Task is opene
            instance.finished_date = None
            if instance.user_story and instance.user_story.status.is_closed == True: # US is close
                us_opened_status = instance.project.us_statuses.filter(
                                                        is_closed=False).order_by(
                                                                          "-order")[0]
                instance.user_story.status = us_opened_status
                instance.user_story.finish_date = None
                instance.user_story.save()

    # Milestone
    if instance.milestone:
        if (instance.status.is_closed and not instance.milestone.closed and
                all([t.status.is_closed for t in instance.milestone.tasks.all()]) and
                all([us.status.is_closed for us in instance.milestone.user_stories.all()])):
            instance.milestone.closed = True
            instance.milestone.save()
        elif not instance.status.is_closed and instance.milestone.closed:
            instance.milestone.closed = False
            instance.milestone.save()
