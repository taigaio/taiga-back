# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from taiga.base.models import NeighborsMixin
from taiga.base.utils.slug import ref_uniquely
from taiga.base.notifications.models import WatchedMixin
from taiga.projects.mixins.blocked.models import BlockedMixin

import reversion


class Issue(NeighborsMixin, WatchedMixin, BlockedMixin):
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                              related_name="owned_issues", verbose_name=_("owner"))
    status = models.ForeignKey("projects.IssueStatus", null=False, blank=False,
                               related_name="issues", verbose_name=_("status"))
    severity = models.ForeignKey("projects.Severity", null=False, blank=False,
                                 related_name="issues", verbose_name=_("severity"))
    priority = models.ForeignKey("projects.Priority", null=False, blank=False,
                                 related_name="issues", verbose_name=_("priority"))
    type = models.ForeignKey("projects.IssueType", null=False, blank=False,
                             related_name="issues", verbose_name=_("type"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True,
                                  default=None, related_name="issues",
                                  verbose_name=_("milestone"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="issues", verbose_name=_("project"))
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
                                    default=None, related_name="issues_assigned_to_me",
                                    verbose_name=_("assigned to"))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      related_name="watched_issues",
                                      verbose_name=_("watchers"))
    tags = PickledObjectField(null=False, blank=True, verbose_name=_("tags"))
    attachments = generic.GenericRelation("projects.Attachment")

    notifiable_fields = [
        "subject",
        "milestone",
        "owner",
        "assigned_to",
        "finished_date",
        "type",
        "status",
        "severity",
        "priority",
        "tags",
        "description",
        "is_blocked",
        "blocked_comment"
    ]

    class Meta:
        verbose_name = "issue"
        verbose_name_plural = "issues"
        ordering = ["project", "created_date"]
        unique_together = ("ref", "project")
        permissions = (
            ("view_issue", "Can view issue"),
        )

    def __str__(self):
        return "({1}) {0}".format(self.ref, self.subject)

    def _get_order_by(self, queryset):
        ordering = self._get_queryset_order_by(queryset)
        if ordering:
            main_order = ordering[0]
            need_extra_ordering = ("severity", "-severity", "owner__first_name",
                                   "-owner__first_name", "status", "-status", "priority",
                                   "-priority", "assigned_to__first_name",
                                   "-assigned_to__first_name")
            if main_order in need_extra_ordering:
                ordering += self._meta.ordering

        return ordering

    def _get_prev_neighbor_filters(self, queryset):
        conds = super()._get_prev_neighbor_filters(queryset)
        try:
            main_order = queryset.query.order_by[0]
        except IndexError:
            main_order = None

        if main_order == "severity":
            conds = [{"severity__order__lt": self.severity.order},
                     {"severity__order": self.severity.order,
                      "created_date__lt": self.created_date}]
        elif main_order == "-severity":
            conds = [{"severity__order__gt": self.severity.order},
                     {"severity__order": self.severity.order,
                      "created_date__lt": self.created_date}]
        elif main_order == "status":
            conds = [{"status__order__lt": self.status.order},
                     {"status__order": self.status.order,
                      "created_date__lt": self.created_date}]
        elif main_order == "-status":
            conds = [{"status__order__gt": self.status.order},
                     {"status__order": self.status.order,
                      "created_date__lt": self.created_date}]
        elif main_order == "priority":
            conds = [{"priority__order__lt": self.priority.order},
                     {"priority__order": self.priority.order,
                      "created_date__lt": self.created_date}]
        elif main_order == "-priority":
            conds = [{"priority__order__gt": self.priority.order},
                     {"priority__order": self.priority.order,
                      "created_date__lt": self.created_date}]
        elif main_order == "owner__first_name":
            conds = [{"owner__first_name": self.owner.first_name,
                      "owner__last_name": self.owner.last_name,
                      "created_date__lt": self.created_date},
                     {"owner__first_name": self.owner.first_name,
                      "owner__last_name__lt": self.owner.last_name},
                     {"owner__first_name__lt": self.owner.first_name}]
        elif main_order == "-owner__first_name":
            conds = [{"owner__first_name": self.owner.first_name,
                      "owner__last_name": self.owner.last_name,
                      "created_date__lt": self.created_date},
                     {"owner__first_name": self.owner.first_name,
                      "owner__last_name__gt": self.owner.last_name},
                     {"owner__first_name__gt": self.owner.first_name}]
        elif main_order == "assigned_to__first_name":
            if self.assigned_to:
                conds = [{"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name": self.assigned_to.last_name,
                          "created_date__lt": self.created_date},
                         {"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name__lt": self.assigned_to.last_name},
                         {"assigned_to__first_name__lt": self.assigned_to.first_name}]
            else:
                conds = [{"assigned_to__isnull": True,
                          "created_date__lt": self.created_date},
                         {"assigned_to__isnull": False}]
        elif main_order == "-assigned_to__first_name":
            if self.assigned_to:
                conds = [{"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name": self.assigned_to.last_name,
                          "created_date__lt": self.created_date},
                         {"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name__gt": self.assigned_to.last_name},
                         {"assigned_to__first_name__gt": self.assigned_to.first_name},
                         {"assigned_to__isnull": True}]
            else:
                conds = [{"assigned_to__isnull": True,
                          "created_date__lt": self.created_date},
                         {"assigned_to__isnull": False}]

        return conds

    def _get_next_neighbor_filters(self, queryset):
        conds = super()._get_next_neighbor_filters(queryset)
        ordering = queryset.query.order_by
        try:
            main_order = ordering[0]
        except IndexError:
            main_order = None

        if main_order == "severity":
            conds = [{"severity__order__gt": self.severity.order},
                     {"severity__order": self.severity.order,
                      "created_date__gt": self.created_date}]
        elif main_order == "-severity":
            conds = [{"severity__order__lt": self.severity.order},
                     {"severity__order": self.severity.order,
                      "created_date__gt": self.created_date}]
        elif main_order == "status":
            conds = [{"status__order__gt": self.status.order},
                     {"status__order": self.status.order,
                      "created_date__gt": self.created_date}]
        elif main_order == "-status":
            conds = [{"status__order__lt": self.status.order},
                     {"status__order": self.status.order,
                      "created_date__gt": self.created_date}]
        elif main_order == "priority":
            conds = [{"priority__order__gt": self.priority.order},
                     {"priority__order": self.priority.order,
                      "created_date__gt": self.created_date}]
        elif main_order == "-priority":
            conds = [{"priority__order__lt": self.priority.order},
                     {"priority__order": self.priority.order,
                      "created_date__gt": self.created_date}]
        elif main_order == "owner__first_name":
            conds = [{"owner__first_name": self.owner.first_name,
                      "owner__last_name": self.owner.last_name,
                      "created_date__gt": self.created_date},
                     {"owner__first_name": self.owner.first_name,
                      "owner__last_name__gt": self.owner.last_name},
                     {"owner__first_name__gt": self.owner.first_name}]
        elif main_order == "-owner__first_name":
            conds = [{"owner__first_name": self.owner.first_name,
                      "owner__last_name": self.owner.last_name,
                      "created_date__gt": self.created_date},
                     {"owner__first_name": self.owner.first_name,
                      "owner__last_name__lt": self.owner.last_name},
                     {"owner__first_name__lt": self.owner.first_name}]
        elif main_order == "assigned_to__first_name":
            if self.assigned_to:
                conds = [{"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name": self.assigned_to.last_name,
                          "created_date__gt": self.created_date},
                         {"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name__gt": self.assigned_to.last_name},
                         {"assigned_to__first_name__gt": self.assigned_to.first_name},
                         {"assigned_to__isnull": True}]
            else:
                conds = [{"assigned_to__isnull": True,
                          "created_date__gt": self.created_date}]
        elif main_order == "-assigned_to__first_name" and self.assigned_to:
                conds = [{"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name": self.assigned_to.last_name,
                          "created_date__gt": self.created_date},
                         {"assigned_to__first_name": self.assigned_to.first_name,
                          "assigned_to__last_name__lt": self.assigned_to.last_name},
                         {"assigned_to__first_name__lt": self.assigned_to.first_name}]
        else:
            conds = [{"assigned_to__isnull": True,
                      "created_date__gt": self.created_date},
                     {"assigned_to__isnull": False}]

        return conds

    @property
    def is_closed(self):
        return self.status.is_closed

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
            "project": self.project,
        }


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Issue)


# Model related signals handlers
@receiver(models.signals.pre_save, sender=Issue, dispatch_uid="issue_finished_date_handler")
def issue_finished_date_handler(sender, instance, **kwargs):
    if instance.status.is_closed and not instance.finished_date:
        instance.finished_date = timezone.now()
    elif not instance.status.is_closed and instance.finished_date:
        instance.finished_date = None


@receiver(models.signals.pre_save, sender=Issue, dispatch_uid="issue_ref_handler")
def issue_ref_handler(sender, instance, **kwargs):
    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, "last_issue_ref", instance.__class__)


@receiver(models.signals.pre_save, sender=Issue, dispatch_uid="issue-tags-normalization")
def issue_tags_normalization(sender, instance, **kwargs):
    if isinstance(instance.tags, (list, tuple)):
        instance.tags = list(map(lambda x: x.lower(), instance.tags))
