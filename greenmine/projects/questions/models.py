# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver

from greenmine.base.utils.slug import ref_uniquely
from greenmine.base.notifications.models import WatchedMixin

from picklefield.fields import PickledObjectField

import reversion


class Question(WatchedMixin):
    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                              related_name="owned_questions", verbose_name=_("owner"))
    status = models.ForeignKey("projects.QuestionStatus", null=False, blank=False,
                               related_name="questions", verbose_name=_("status"))
    subject = models.CharField(max_length=250, null=False, blank=False,
                               verbose_name=_("subject"))
    content = models.TextField(null=False, blank=True, verbose_name=_("content"))
    closed = models.BooleanField(default=False, null=False, blank=True,
                                 verbose_name=_("closed"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="questions", verbose_name=_("project"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True,
                                  default=None, related_name="questions",
                                  verbose_name=_("milestone"))
    finished_date = models.DateTimeField(null=True, blank=True,
                                         verbose_name=_("finished date"))
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    default=None, related_name="questions_assigned_to_me",
                                    verbose_name=_("assigned_to"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      related_name="watched_questions",
                                      verbose_name=_("watchers"))
    tags = PickledObjectField(null=False, blank=True, verbose_name=_("tags"))

    notifiable_fields = [
        "owner",
        "status",
        "milestone",
        "finished_date",
        "subject",
        "content",
        "assigned_to",
        "tags"
    ]

    class Meta:
        verbose_name = "question"
        verbose_name_plural = "questions"
        ordering = ["project", "created_date", "subject"]
        unique_together = ("ref", "project")
        permissions = (
            ("reply_question", _("Can reply questions")),
            ("change_owned_question", _("Can modify owned questions")),
            ("change_assigned_question", _("Can modify assigned questions")),
            ("assign_question_to_other", _("Can assign questions to others")),
            ("assign_question_to_myself", _("Can assign questions to myself")),
            ("change_question_state", _("Can change the question state")),
            ("view_question", _("Can view the question")),
        )

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if self.id:
            self.modified_date = timezone.now()
        super(Question, self).save(*args, **kwargs)

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
reversion.register(Question)


# Model related signals handlers
@receiver(models.signals.pre_save, sender=Question, dispatch_uid="question_ref_handler")
def question_ref_handler(sender, instance, **kwargs):
    if not instance.id and instance.project:
        instance.ref = ref_uniquely(instance.project,"last_question_ref",
                                    instance.__class__)
