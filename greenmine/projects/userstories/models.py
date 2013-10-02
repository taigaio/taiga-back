# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from greenmine.base.utils.slug import ref_uniquely
from greenmine.base.notifications.models import WatchedMixin

import reversion


class UserStoryStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="us_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = u"user story status"
        verbose_name_plural = u"user story statuses"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class Points(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    value = models.FloatField(default=None, null=True, blank=True,
                              verbose_name=_("value"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="points", verbose_name=_("project"))

    class Meta:
        verbose_name = u"point"
        verbose_name_plural = u"points"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class RolePoints(models.Model):
    user_story = models.ForeignKey("UserStory", null=False, blank=False,
                                   related_name="role_points",
                                   verbose_name=_("user story"))
    role = models.ForeignKey("users.Role", null=False, blank=False,
                             related_name="role_points",
                             verbose_name=_("role"))
    points = models.ForeignKey("Points", null=False, blank=False,
                               related_name="role_points",
                               verbose_name=_("points"))

    class Meta:
        unique_together = ("user_story", "role")


class UserStory(WatchedMixin, models.Model):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                            verbose_name=_("uuid"))
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True, default=None,
                                  related_name="user_stories", verbose_name=_("milestone"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="user_stories", verbose_name=_("project"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_user_stories", verbose_name=_("owner"))
    status = models.ForeignKey("UserStoryStatus", null=False, blank=False,
                               related_name="user_stories", verbose_name=_("status"))
    points = models.ManyToManyField("Points", null=False, blank=False,
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

    notifiable_fields = [
        "milestone",
        "owner",
        "status",
        "points",
        "finish_date",
        "subject",
        "description",
        "client_requirement",
        "team_requirement",
        "tags",
    ]

    class Meta:
        verbose_name = u"user story"
        verbose_name_plural = u"user stories"
        ordering = ["project", "order"]
        unique_together = ("ref", "project")
        permissions = (
            ("comment_userstory", "Can comment user stories"),
            ("view_userstory", "Can view user stories"),
            ("change_owned_userstory", "Can modify owned user stories"),
            ("add_userstory_to_milestones", "Can add user stories to milestones"),
        )

    def __unicode__(self):
        return u"({1}) {0}".format(self.ref, self.subject)

    def __repr__(self):
        return u"<UserStory %s>" % (self.id)

    @property
    def is_closed(self):
        return self.status.is_closed

    def get_role_points(self):
        return self.role_points

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
