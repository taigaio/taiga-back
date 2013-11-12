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


class Issue(WatchedMixin):
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
            "project_owner": (self.project, self.project.owner),
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
