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


class Priority(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="priorities", verbose_name=_("project"))

    class Meta:
        verbose_name = u"priority"
        verbose_name_plural = u"priorities"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class Severity(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="severities", verbose_name=_("project"))

    class Meta:
        verbose_name = u"severity"
        verbose_name_plural = u"severities"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class IssueStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="issue_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = u"issue status"
        verbose_name_plural = u"issue statuses"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class IssueType(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="issue_types", verbose_name=_("project"))

    class Meta:
        verbose_name = u"issue type"
        verbose_name_plural = u"issue types"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __unicode__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class Issue(models.Model, WatchedMixin):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                            verbose_name=_("uuid"))
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                              related_name="owned_issues", verbose_name=_("owner"))
    status = models.ForeignKey("IssueStatus", null=False, blank=False, related_name="issues",
                               verbose_name=_("status"))
    severity = models.ForeignKey("Severity", null=False, blank=False, related_name="issues",
                                 verbose_name=_("severity"))
    priority = models.ForeignKey("Priority", null=False, blank=False, related_name="issues",
                                 verbose_name=_("priority"))
    type = models.ForeignKey("IssueType", null=False, blank=False, related_name="issues",
                             verbose_name=_("type"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True, default=None,
                               related_name="issues", verbose_name=_("milestone"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="issues", verbose_name=_("project"))
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
                                    default=None, related_name="issues_assigned_to_me",
                                    verbose_name=_("assigned to"))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      related_name="watched_issues",
                                      verbose_name=_("watchers"))
    tags = PickledObjectField(null=False, blank=True, verbose_name=_("tags"))

    notifiable_fields = [
         "owner",
         "status",
         "severity",
         "priority",
         "type",
         "milestone",
         "finished_date",
         "subject",
         "description",
         "assigned_to",
         "tags",
    ]

    class Meta:
        verbose_name = u"issue"
        verbose_name_plural = u"issues"
        ordering = ["project", "created_date"]
        unique_together = ("ref", "project")
        permissions = (
            ("comment_issue", "Can comment issues"),
            ("change_owned_issue", "Can modify owned issues"),
            ("change_assigned_issue", "Can modify assigned issues"),
            ("assign_issue_to_other", "Can assign issues to others"),
            ("assign_issue_to_myself", "Can assign issues to myself"),
            ("change_issue_state", "Can change the issue state"),
            ("view_issue", "Can view the issue"),
        )

    def __unicode__(self):
        return u"({1}) {0}".format(self.ref, self.subject)

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()
        super(Issue, self).save(*args, **kwargs)

    @property
    def is_closed(self):
        return self.status.is_closed

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
@receiver(models.signals.pre_save, sender=Issue, dispatch_uid="issue_ref_handler")
def issue_ref_handler(sender, instance, **kwargs):
    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project, "last_issue_ref", instance.__class__)
