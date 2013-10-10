# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from greenmine.base.utils.slug import ref_uniquely
from greenmine.base.notifications.models import WatchedMixin

import reversion


class Task(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                            verbose_name=_("uuid"))
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
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True, default=None,
                               related_name="tasks", verbose_name=_("milestone"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
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
    is_iocaine = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is iocaine"))

    notifiable_fields = [
        "owner",
        "status",
        "finished_date",
        "subject",
        "description",
        "assigned_to",
        "tags",
        "is_iocaine",
    ]

    class Meta:
        verbose_name = u"task"
        verbose_name_plural = u"tasks"
        ordering = ["project", "created_date"]
        unique_together = ("ref", "project")
        permissions = (
            ("comment_task", "Can comment tasks"),
            ("change_owned_task", "Can modify owned tasks"),
            ("change_assigned_task", "Can modify assigned tasks"),
            ("assign_task_to_other", "Can assign tasks to others"),
            ("assign_task_to_myself", "Can assign tasks to myself"),
            ("change_task_state", "Can change the task state"),
            ("view_task", "Can view the task"),
            ("add_task_to_us", "Can add tasks to a user story"),
        )

    def __str__(self):
        return u"({1}) {0}".format(self.ref, self.subject)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()

        super(Task, self).save(*args, **kwargs)

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
    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, "last_task_ref", instance.__class__)


@receiver(models.signals.pre_save, sender=Task, dispatch_uid="tasks_close_handler")
def tasks_close_handler(sender, instance, **kwargs):
    """
    Automatically assignes a seguent reference code to a
    user story if that is not created.
    """
    if instance.id:
        if (sender.objects.get(id=instance.id).status.is_closed == False and
                instance.status.is_closed == True):
            instance.finished_date = timezone.now()
            if (all([task.status.is_closed for task in
                    instance.user_story.tasks.exclude(id=instance.id)])):
                instance.user_story.finish_date = timezone.now()
                instance.user_story.save()
        elif (sender.objects.get(id=instance.id).status.is_closed == True and
                instance.status.is_closed == False):
            instance.finished_date = None
            if instance.user_story:
                instance.user_story.finish_date = None
                instance.user_story.save()
    elif instance.user_story:
        instance.user_story.finish_date = None
        instance.user_story.save()
