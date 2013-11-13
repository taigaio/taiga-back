# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.contenttypes import generic
from django.conf import settings
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField
import reversion

from greenmine.base.utils.slug import ref_uniquely
from greenmine.base.notifications.models import WatchedMixin



class RolePoints(models.Model):
    user_story = models.ForeignKey("UserStory", null=False, blank=False,
                                   related_name="role_points",
                                   verbose_name=_("user story"))
    role = models.ForeignKey("users.Role", null=False, blank=False,
                             related_name="role_points",
                             verbose_name=_("role"))
    points = models.ForeignKey("projects.Points", null=False, blank=False,
                               related_name="role_points",
                               verbose_name=_("points"))

    class Meta:
        verbose_name = "role points"
        verbose_name_plural = "role points"
        unique_together = ("user_story", "role")
        ordering = ["user_story", "role"]
        permissions = (
            ("view_rolepoints", "Can view role points"),
        )
    def __str__(self):
        return "{}: {}".format(self.role.name, self.points.name)


class UserStory(WatchedMixin):
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True,
                                  default=None, related_name="user_stories",
                                  on_delete=models.SET_NULL, verbose_name=_("milestone"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="user_stories", verbose_name=_("project"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_user_stories", verbose_name=_("owner"),
                              on_delete=models.SET_NULL)
    status = models.ForeignKey("projects.UserStoryStatus", null=True, blank=True,
                               related_name="user_stories", verbose_name=_("status"),
                               on_delete=models.SET_NULL)
    points = models.ManyToManyField("projects.Points", null=False, blank=False,
                                    related_name="userstories", through="RolePoints",
                                    verbose_name=_("points"))
    order = models.PositiveSmallIntegerField(null=False, blank=False, default=100,
                                             verbose_name=_("order"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    finish_date = models.DateTimeField(null=True, blank=True,
                                       verbose_name=_("finish date"))
    subject = models.CharField(max_length=500, null=False, blank=False,
                               verbose_name=_("subject"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      related_name="watched_us", verbose_name=_("watchers"))
    client_requirement = models.BooleanField(default=False, null=False, blank=True,
                                             verbose_name=_("is client requirement"))
    team_requirement = models.BooleanField(default=False, null=False, blank=True,
                                           verbose_name=_("is team requirement"))
    tags = PickledObjectField(null=False, blank=True,
                              verbose_name=_("tags"))
    attachments = generic.GenericRelation("projects.Attachment")

    notifiable_fields = [
        "subject",
        "milestone",
        "owner",
        "finish_date",
        "client_requirement",
        "team_requirement",
        "status",
        "points",
        "tags",
        "description",
    ]

    class Meta:
        verbose_name = "user story"
        verbose_name_plural = "user stories"
        ordering = ["project", "order"]
        unique_together = ("ref", "project")
        permissions = (
            ("view_userstory", "Can view user story"),
        )

    def __str__(self):
        return "({1}) {0}".format(self.ref, self.subject)

    def __repr__(self):
        return "<UserStory %s>" % (self.id)

    @property
    def is_closed(self):
        return self.status.is_closed

    def get_role_points(self):
        return self.role_points

    def get_total_points(self):
        total = 0.0
        for rp in self.role_points.select_related("points"):
            if rp.points.value:
                total += rp.points.value

        return total

    def get_notifiable_tags_display(self, value):
        if type(value) is list:
            return ", ".join(value)
        return value

    def get_notifiable_points_display(self, value):
        if isinstance(value, models.manager.Manager):
            return ", ".join(["{}: {}".format(rp.role.name,rp.points.name)
                              for rp in self.role_points.all().order_by("role")])

        return None

    def _get_watchers_by_role(self):
        return {
            "owner": self.owner,
            "suscribed_watchers": self.watchers.all(),
            "project_owner": (self.project, self.project.owner),
        }


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(UserStory)


# Model related signals handlers
@receiver(models.signals.pre_save, sender=UserStory, dispatch_uid="user_story_ref_handler")
def us_ref_handler(sender, instance, **kwargs):
    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, "last_us_ref", instance.__class__)


@receiver(models.signals.post_save, sender=UserStory,
          dispatch_uid="user_story_create_role_points_handler")
def us_create_role_points_handler(sender, instance, **kwargs):
    instance.project.update_role_points()


@receiver(models.signals.post_save, sender=UserStory,
          dispatch_uid="user_story_tasks_reassignation")
def us_task_reassignation(sender, instance, created, **kwargs):
    if not created:
        instance.tasks.update(milestone=instance.milestone)

@receiver(models.signals.pre_save, sender=UserStory, dispatch_uid="us-tags-normalization")
def us_tags_normalization(sender, instance, **kwargs):
    if isinstance(instance.tags, (list, tuple)):
        instance.tags = list(map(lambda x: x.lower(), instance.tags))
