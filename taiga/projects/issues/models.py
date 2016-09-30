# -*- coding: utf-8 -*-
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

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from taiga.projects.occ import OCCModelMixin
from taiga.projects.notifications.mixins import WatchedModelMixin
from taiga.projects.mixins.blocked import BlockedMixin
from taiga.projects.tagging.models import TaggedMixin


class Issue(OCCModelMixin, WatchedModelMixin, BlockedMixin, TaggedMixin, models.Model):
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                              related_name="owned_issues", verbose_name=_("owner"))
    status = models.ForeignKey("projects.IssueStatus", null=True, blank=True,
                               related_name="issues", verbose_name=_("status"))
    severity = models.ForeignKey("projects.Severity", null=True, blank=True,
                                 related_name="issues", verbose_name=_("severity"))
    priority = models.ForeignKey("projects.Priority", null=True, blank=True,
                                 related_name="issues", verbose_name=_("priority"))
    type = models.ForeignKey("projects.IssueType", null=True, blank=True,
                             related_name="issues", verbose_name=_("type"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True,
                                  default=None, related_name="issues",
                                  verbose_name=_("milestone"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="issues", verbose_name=_("project"))
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
                                    default=None, related_name="issues_assigned_to_me",
                                    verbose_name=_("assigned to"))
    attachments = GenericRelation("attachments.Attachment")
    external_reference = ArrayField(models.TextField(null=False, blank=False),
                                    null=True, blank=True, default=None, verbose_name=_("external reference"))
    _importing = None

    class Meta:
        verbose_name = "issue"
        verbose_name_plural = "issues"
        ordering = ["project", "-id"]
        permissions = (
            ("view_issue", "Can view issue"),
        )

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_date = timezone.now()

        if not self.status_id:
            self.status = self.project.default_issue_status

        if not self.type_id:
            self.type = self.project.default_issue_type

        if not self.severity_id:
            self.severity = self.project.default_severity

        if not self.priority_id:
            self.priority = self.project.default_priority

        return super().save(*args, **kwargs)

    def __str__(self):
        return "({1}) {0}".format(self.ref, self.subject)

    @property
    def is_closed(self):
        return self.status is not None and self.status.is_closed
