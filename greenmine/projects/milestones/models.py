# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from greenmine.base.utils.slug import slugify_uniquely
from greenmine.base.utils.dicts import dict_sum
from greenmine.base.notifications.models import WatchedMixin

from greenmine.projects.userstories.models import UserStory

import reversion
import itertools
import datetime


class Milestone(WatchedMixin):
    name = models.CharField(max_length=200, db_index=True, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                            verbose_name=_("slug"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_milestones", verbose_name=_("owner"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="milestones", verbose_name=_("project"))
    estimated_start = models.DateField(null=True, blank=True, default=None,
                                       verbose_name=_("estimated start"))
    estimated_finish = models.DateField(null=True, blank=True, default=None,
                                        verbose_name=_("estimated finish"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    closed = models.BooleanField(default=False, null=False, blank=True,
                                 verbose_name=_("is closed"))
    disponibility = models.FloatField(default=0.0, null=True, blank=True,
                                      verbose_name=_("disponibility"))
    order = models.PositiveSmallIntegerField(default=1, null=False, blank=False,
                                             verbose_name=_("order"))

    notifiable_fields = [
        "name",
        "owner",
        "disponibility",
        "closed",
        "estimated_start",
        "estimated_finish",
    ]

    class Meta:
        verbose_name = "milestone"
        verbose_name_plural = "milestones"
        ordering = ["project", "created_date"]
        unique_together = ("name", "project")
        permissions = (
            ("view_milestone", "Can view milestone"),
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Milestone {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super().save(*args, **kwargs)

    def _get_user_stories_points(self, user_stories):
        role_points = [us.role_points.all() for us in user_stories]
        flat_role_points = itertools.chain(*role_points)
        flat_role_dicts = map(lambda x: {x.role_id: x.points.value if x.points.value else 0}, flat_role_points)
        return dict_sum(*flat_role_dicts)

    @property
    def total_points(self):
        return self._get_user_stories_points(
            [us for us in self.user_stories.all()]
        )

    @property
    def closed_points(self):
        return self._get_user_stories_points(
            [us for us in self.user_stories.all() if us.is_closed]
        )

    def _get_points_increment(self, client_requirement, team_requirement):
        user_stories = UserStory.objects.none()
        if self.estimated_start and self.estimated_finish:
            user_stories = UserStory.objects.filter(
                created_date__gte=self.estimated_start,
                created_date__lt=self.estimated_finish,
                project_id=self.project_id,
                client_requirement=client_requirement,
                team_requirement=team_requirement
            )
        return self._get_user_stories_points(user_stories)

    @property
    def client_increment_points(self):
        client_increment = self._get_points_increment(True, False)
        shared_increment = {
            key: value/2 for key, value in self.shared_increment_points.items()
        }
        return dict_sum(client_increment, shared_increment)

    @property
    def team_increment_points(self):
        team_increment = self._get_points_increment(False, True)
        shared_increment = {
            key: value/2 for key, value in self.shared_increment_points.items()
        }
        return dict_sum(team_increment, shared_increment)

    @property
    def shared_increment_points(self):
        return self._get_points_increment(True, True)

    def _get_watchers_by_role(self):
        return {
            "owner": self.owner,
            "project_owner": (self.project, self.project.owner),
        }

    def closed_points_by_date(self, date):
        return self._get_user_stories_points([
            us for us in self.user_stories.filter(
                finish_date__lt=date + datetime.timedelta(days=1)
            ) if us.is_closed
        ])


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Milestone)
