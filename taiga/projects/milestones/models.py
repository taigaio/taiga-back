# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.apps import apps
from django.db import models
from django.db.models import Prefetch, Count
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property

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
    _total_closed_points_by_date = None

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

    @cached_property
    def cached_user_stories(self):
        return (self.user_stories.prefetch_related("role_points", "role_points__points")
                                 .annotate(num_tasks=Count("tasks")))

    def _get_user_stories_points(self, user_stories):
        role_points = [us.role_points.all() for us in user_stories]
        flat_role_points = itertools.chain(*role_points)
        flat_role_dicts = map(lambda x: {x.role_id: x.points.value if x.points.value else 0}, flat_role_points)
        return dict_sum(*flat_role_dicts)

    @property
    def total_points(self):
        return self._get_user_stories_points(
            [us for us in self.cached_user_stories]
        )

    @property
    def closed_points(self):
        return self._get_user_stories_points(
            [us for us in self.cached_user_stories if us.is_closed]
        )

    def total_closed_points_by_date(self, date):
        # Milestone instance will keep a cache of the total closed points by date
        if self._total_closed_points_by_date is None:
            self._total_closed_points_by_date = {}

            # We need to keep the milestone user stories indexed by id in a dict
            user_stories = {}
            for us in self.cached_user_stories:
                us._total_us_points = sum(self._get_user_stories_points([us]).values())
                user_stories[us.id] = us

            tasks = self.tasks.\
                    select_related("user_story").\
                    exclude(finished_date__isnull=True).\
                    exclude(user_story__isnull=True)

            # For each finished task we try to know the proporional part of points
            # it represetnts from the user story and add it to the closed points
            # for that date
            # This calulation is the total user story points divided by its number of tasks
            for task in tasks:
                user_story = user_stories[task.user_story.id]
                total_us_points = user_story._total_us_points
                us_tasks_counter = user_story.num_tasks

                # If the task was finished before starting the sprint it needs
                # to be included
                finished_date = task.finished_date.date()
                if finished_date < self.estimated_start:
                    finished_date = self.estimated_start

                points_by_date = self._total_closed_points_by_date.get(finished_date, 0)
                points_by_date += total_us_points / us_tasks_counter
                self._total_closed_points_by_date[finished_date] = points_by_date

            # At this point self._total_closed_points_by_date keeps a dict where the
            # finished date of the task is the key and the value is the increment of points
            # We are transforming this dict of increments in an acumulation one including
            # all the dates from the sprint

            acumulated_date_points = 0
            current_date = self.estimated_start
            while current_date <= self.estimated_finish:
                acumulated_date_points += self._total_closed_points_by_date.get(current_date, 0)
                self._total_closed_points_by_date[current_date] = acumulated_date_points
                current_date = current_date + datetime.timedelta(days=1)

        return self._total_closed_points_by_date.get(date, 0)
