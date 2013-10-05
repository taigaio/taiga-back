# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from greenmine.base.utils.slug import slugify_uniquely
from greenmine.base.notifications.models import WatchedMixin

import reversion


class Milestone(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                            verbose_name=_("uuid"))
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
        "estimated_start",
        "estimated_finish",
        "closed",
        "disponibility",
    ]

    class Meta:
        verbose_name = u"milestone"
        verbose_name_plural = u"milestones"
        ordering = ["project", "-created_date"]
        unique_together = ("name", "project")
        permissions = (
            ("view_milestone", "Can view milestones"),
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return u"<Milestone {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Milestone, self).save(*args, **kwargs)

    @property
    def closed_points(self):
        # TODO: refactor or remove
        #points = [ us.points.value for us in self.user_stories.all() if us.is_closed ]
        #return sum(points)
        return 0

    @property
    def client_increment_points(self):
        # TODO: refactor or remove
        #user_stories = UserStory.objects.filter(
        #    created_date__gte=self.estimated_start,
        #    created_date__lt=self.estimated_finish,
        #    project_id = self.project_id,
        #    client_requirement=True,
        #    team_requirement=False
        #)
        #points = [ us.points.value for us in user_stories ]
        #return sum(points) + (self.shared_increment_points / 2)
        return 0

    @property
    def team_increment_points(self):
        # TODO: refactor or remove
        #user_stories = UserStory.objects.filter(
        #    created_date__gte=self.estimated_start,
        #    created_date__lt=self.estimated_finish,
        #    project_id = self.project_id,
        #    client_requirement=False,
        #    team_requirement=True
        #)
        #points = [ us.points.value for us in user_stories ]
        #return sum(points) + (self.shared_increment_points / 2)
        return 0

    @property
    def shared_increment_points(self):
        # TODO: refactor or remove
        #user_stories = UserStory.objects.filter(
        #    created_date__gte=self.estimated_start,
        #    created_date__lt=self.estimated_finish,
        #    project_id = self.project_id,
        #    client_requirement=True,
        #    team_requirement=True
        #)
        #points = [ us.points.value for us in user_stories ]
        #return sum(points)
        return 0

    def _get_watchers_by_role(self):
        return {
            "owner": self.owner,
            "project_owner": (self.project, self.project.owner),
        }


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Milestone)
