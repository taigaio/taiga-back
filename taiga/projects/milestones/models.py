# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from taiga.base.utils.slug import slugify_uniquely
from taiga.base.utils.dicts import dict_sum
from taiga.projects.notifications.mixins import WatchedModelMixin
from taiga.projects.userstories.models import UserStory

import itertools
import datetime


class Milestone(WatchedModelMixin, models.Model):
    name = models.CharField(max_length=200, db_index=True, null=False, blank=False,
                            verbose_name=_("name"))
    # TODO: Change the unique restriction to a unique together with the project id
    slug = models.SlugField(max_length=250, db_index=True, null=False, blank=True,
                            verbose_name=_("slug"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_milestones", verbose_name=_("owner"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="milestones", verbose_name=_("project"))
    estimated_start = models.DateField(verbose_name=_("estimated start date"))
    estimated_finish = models.DateField(verbose_name=_("estimated finish date"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    closed = models.BooleanField(default=False, null=False, blank=True,
                                 verbose_name=_("is closed"))
    disponibility = models.FloatField(default=0.0, null=True, blank=True,
                                      verbose_name=_("disponibility"))
    order = models.PositiveSmallIntegerField(default=1, null=False, blank=False,
                                             verbose_name=_("order"))
    _importing = None

    class Meta:
        verbose_name = "milestone"
        verbose_name_plural = "milestones"
        ordering = ["project", "created_date"]
        unique_together = [("name", "project"), ("slug", "project")]
        permissions = (
            ("view_milestone", "Can view milestone"),
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Milestone {0}>".format(self.id)

    def clean(self):
        # Don't allow draft entries to have a pub_date.
        if self.estimated_start and self.estimated_finish and self.estimated_start > self.estimated_finish:
            raise ValidationError(_('The estimated start must be previous to the estimated finish.'))

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_date = timezone.now()
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

    def _get_increment_points(self):
        if hasattr(self, "_increments"):
            return self._increments

        self._increments = {
            "client_increment": {},
            "team_increment": {},
            "shared_increment": {},
        }
        user_stories = UserStory.objects.none()
        if self.estimated_start and self.estimated_finish:
            user_stories = filter(
                lambda x: x.created_date.date() >= self.estimated_start and x.created_date.date() < self.estimated_finish,
                self.project.user_stories.all()
            )
            self._increments['client_increment'] = self._get_user_stories_points(
                [us for us in user_stories if us.client_requirement is True and us.team_requirement is False]
            )
            self._increments['team_increment'] = self._get_user_stories_points(
                [us for us in user_stories if us.client_requirement is False and us.team_requirement is True]
            )
            self._increments['shared_increment'] = self._get_user_stories_points(
                [us for us in user_stories if us.client_requirement is True and us.team_requirement is True]
            )
        return self._increments


    @property
    def client_increment_points(self):
        self._get_increment_points()
        client_increment = self._get_increment_points()["client_increment"]
        shared_increment = {
            key: value/2 for key, value in self._get_increment_points()["shared_increment"].items()
        }
        return dict_sum(client_increment, shared_increment)

    @property
    def team_increment_points(self):
        team_increment = self._get_increment_points()["team_increment"]
        shared_increment = {
            key: value/2 for key, value in self._get_increment_points()["shared_increment"].items()
        }
        return dict_sum(team_increment, shared_increment)

    @property
    def shared_increment_points(self):
        return self._get_increment_points()["shared_increment"]

    def closed_points_by_date(self, date):
        return self._get_user_stories_points([
            us for us in self.user_stories.filter(
                finish_date__lt=date + datetime.timedelta(days=1)
            ).prefetch_related('role_points', 'role_points__points') if us.is_closed
        ])
