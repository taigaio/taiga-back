# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.loading import get_model
from django.conf import settings
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from picklefield.fields import PickledObjectField

from greenmine.base.utils.slug import slugify_uniquely
from greenmine.base.notifications.models import WatchedMixin
from . import choices

import reversion


class Attachment(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                              related_name="change_attachments", verbose_name=_("owner"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="attachments", verbose_name=_("project"))
    content_type = models.ForeignKey(ContentType, null=False, blank=False,
                                     verbose_name=_("content type"))
    object_id = models.PositiveIntegerField(null=False, blank=False,
                                            verbose_name=_("object id"))
    content_object = generic.GenericForeignKey("content_type", "object_id")
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    attached_file = models.FileField(max_length=500, null=True, blank=True,
                                     upload_to="files/msg", verbose_name=_("attached file"))

    class Meta:
        verbose_name = u"attachment"
        verbose_name_plural = u"attachments"
        ordering = ["project", "created_date"]

    def __str__(self):
        return u"content_type {0} - object_id {1} - attachment {2}".format(
                self.content_type, self.object_id, self.id)


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                             related_name="memberships")
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="memberships")
    role = models.ForeignKey("users.Role", null=False, blank=False,
                             related_name="memberships")

    class Meta:
        unique_together = ("user", "project")


class Project(models.Model):
    uuid = models.CharField(max_length=40, unique=True, null=False, blank=True,
                            verbose_name=_("uuid"))
    name = models.CharField(max_length=250, unique=True, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                            verbose_name=_("slug"))
    description = models.TextField(null=False, blank=False,
                                   verbose_name=_("description"))
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                              related_name="owned_projects", verbose_name=_("owner"))
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="projects",
                                     through="Membership", verbose_name=_("members"))
    public = models.BooleanField(default=True, null=False, blank=True,
                                 verbose_name=_("public"))
    last_us_ref = models.BigIntegerField(null=True, blank=False, default=1,
                                         verbose_name=_("last us ref"))
    last_task_ref = models.BigIntegerField(null=True, blank=False, default=1,
                                           verbose_name=_("last task ref"))
    last_issue_ref = models.BigIntegerField(null=True, blank=False, default=1,
                                            verbose_name=_("last issue ref"))
    total_milestones = models.IntegerField(default=0, null=True, blank=True,
                                           verbose_name=_("total of milestones"))
    total_story_points = models.FloatField(default=None, null=True, blank=False,
                                           verbose_name=_("total story points"))
    tags = PickledObjectField(null=False, blank=True,
                              verbose_name=_("tags"))
    class Meta:
        verbose_name = u"project"
        verbose_name_plural = u"projects"
        ordering = ["name"]
        permissions = (
            ("list_projects", "Can list projects"),
            ("view_project", "Can view project"),
            ("manage_users", "Can manage users"),
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return u"<Project {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Project, self).save(*args, **kwargs)

    @property
    def list_of_milestones(self):
        return [{
            "id": milestone.id,
            "name": milestone.name,
            "finish_date": milestone.estimated_finish,
            "closed_points": milestone.closed_points,
            "client_increment_points": milestone.client_increment_points,
            "team_increment_points": milestone.team_increment_points
        } for milestone in self.milestones.all().order_by("estimated_start")]

    def get_roles(self):
        role_model = get_model("users", "Role")
        return role_model.objects.filter(id__in=list(self.memberships.values_list(
                                                                 "role", flat=True)))
    def get_users(self):
        user_model = get_user_model()
        return user_model.objects.filter(id__in=list(self.memberships.values_list(
                                                                 "user", flat=True)))
    def update_role_points(self):
        rolepoints_model = get_model("userstories", "RolePoints")

        # Get all available roles on this project
        roles = self.get_roles().filter(computable=True)

        # Get point instance that represent a null/undefined
        null_points_value = self.points.get(value=None)

        # Iter over all project user stories and create
        # role point instance for new created roles.
        for us in self.user_stories.all():
            for role in roles:
                if not us.role_points.filter(role=role).exists():
                    sp = rolepoints_model.objects.create(role=role, user_story=us,
                                                         points=null_points_value)

        # Now remove rolepoints associated with not existing roles.
        rp_query = rolepoints_model.objects.filter(user_story__in=self.user_stories.all())
        rp_query = rp_query.exclude(role__id__in=roles.values_list("id", flat=True))
        rp_query.delete()


# User Stories common Models

class UserStoryStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="us_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = u"user story status"
        verbose_name_plural = u"user story statuses"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class Points(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    value = models.FloatField(default=None, null=True, blank=True,
                              verbose_name=_("value"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="points", verbose_name=_("project"))

    class Meta:
        verbose_name = u"point"
        verbose_name_plural = u"points"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


# Tasks common models

class TaskStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="task_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = u"task status"
        verbose_name_plural = u"task statuses"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


# Issue common Models

class Priority(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="priorities", verbose_name=_("project"))

    class Meta:
        verbose_name = u"priority"
        verbose_name_plural = u"priorities"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class Severity(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="severities", verbose_name=_("project"))

    class Meta:
        verbose_name = u"severity"
        verbose_name_plural = u"severities"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class IssueStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="issue_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = u"issue status"
        verbose_name_plural = u"issue statuses"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


class IssueType(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False, verbose_name=_("order"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="issue_types", verbose_name=_("project"))

    class Meta:
        verbose_name = u"issue type"
        verbose_name_plural = u"issue types"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


# Questions common models

class QuestionStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="question_status",
                                verbose_name=_("project"))

    class Meta:
        verbose_name = u"question status"
        verbose_name_plural = u"question status"
        ordering = ["project", "name"]
        unique_together = ("project", "name")

    def __str__(self):
        return u"project {0} - {1}".format(self.project_id, self.name)


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Project)

# On membership object is created/changed, update
# role-points relation.
@receiver(models.signals.post_save, sender=Membership,
          dispatch_uid='membership_post_save')
def membership_post_save(sender, instance, created, **kwargs):
    instance.project.update_role_points()


# On membership object is deleted, update role-points relation.
@receiver(models.signals.pre_delete, sender=Membership,
          dispatch_uid='membership_pre_delete')
def membership_post_delete(sender, instance, using, **kwargs):
    instance.project.update_role_points()


@receiver(models.signals.post_save, sender=Project, dispatch_uid='project_post_save')
def project_post_save(sender, instance, created, **kwargs):
    """
    Create all project model depences on project is
    created.
    """
    if not created:
        return

    # Populate new project dependen default data

    # USs
    for order, name, value in choices.POINTS_CHOICES:
        Points.objects.create(project=instance, name=name, order=order, value=value)

    for order, name, is_closed in choices.US_STATUSES:
        UserStoryStatus.objects.create(name=name, order=order,
                                             is_closed=is_closed, project=instance)

    # Tasks
    for order, name, is_closed, color in choices.TASK_STATUSES:
        TaskStatus.objects.create(name=name, order=order, color=color,
                                        is_closed=is_closed, project=instance)

    # Issues
    for order, name in choices.PRIORITY_CHOICES:
        Priority.objects.create(project=instance, name=name, order=order)

    for order, name in choices.SEVERITY_CHOICES:
        Severity.objects.create(project=instance, name=name, order=order)

    for order, name, is_closed in choices.ISSUE_STATUSES:
        IssueStatus.objects.create(name=name, order=order,
                                         is_closed=is_closed, project=instance)

    for order, name in choices.ISSUE_TYPES:
        IssueType.objects.create(project=instance, name=name, order=order)

    # Questions
    for order, name, is_closed in choices.QUESTION_STATUS:
        QuestionStatus.objects.create(name=name, order=order,
                                            is_closed=is_closed, project=instance)
