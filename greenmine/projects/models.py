# -*- coding: utf-8 -*-

import itertools
import collections

from django.db import models
from django.db.models.loading import get_model
from django.conf import settings
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from picklefield.fields import PickledObjectField
import reversion


from greenmine.base.utils.slug import slugify_uniquely
from greenmine.base.utils.dicts import dict_sum
from greenmine.projects.userstories.models import UserStory
from . import choices


class Membership(models.Model):
    # This model stores all project memberships. Also
    # stores invitations to memberships that does not have
    # assigned user.

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None,
                             related_name="memberships")
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="memberships")
    role = models.ForeignKey("users.Role", null=False, blank=False,
                             related_name="memberships")

    # Invitation metadata
    email = models.EmailField(max_length=255, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
    token = models.CharField(max_length=60, unique=True, blank=True, null=True,
                             default=None)

    class Meta:
        verbose_name = "membership"
        verbose_name_plural = "membershipss"
        ordering = ["project", "role"]
        permissions = (
            ("view_membership", "Can view membership"),
        )



class ProjectDefaults(models.Model):
    default_points = models.OneToOneField("projects.Points", on_delete=models.SET_NULL,
                                          related_name="+", null=True, blank=True,
                                          verbose_name=_("default points"))
    default_us_status = models.OneToOneField("projects.UserStoryStatus",
                                             on_delete=models.SET_NULL, related_name="+",
                                             null=True, blank=True,
                                             verbose_name=_("default US status"))
    default_task_status = models.OneToOneField("projects.TaskStatus",
                                               on_delete=models.SET_NULL, related_name="+",
                                               null=True, blank=True,
                                               verbose_name=_("default task status"))
    default_priority = models.OneToOneField("projects.Priority", on_delete=models.SET_NULL,
                                            related_name="+", null=True, blank=True,
                                            verbose_name=_("default priority"))
    default_severity = models.OneToOneField("projects.Severity", on_delete=models.SET_NULL,
                                            related_name="+", null=True, blank=True,
                                            verbose_name=_("default severity"))
    default_issue_status = models.OneToOneField("projects.IssueStatus",
                                                on_delete=models.SET_NULL, related_name="+",
                                                null=True, blank=True,
                                                verbose_name=_("default issue status"))
    default_issue_type = models.OneToOneField("projects.IssueType",
                                              on_delete=models.SET_NULL, related_name="+",
                                              null=True, blank=True,
                                              verbose_name=_("default issue type"))
    default_question_status = models.OneToOneField("projects.QuestionStatus",
                                                   on_delete=models.SET_NULL,
                                                   related_name="+", null=True, blank=True,
                                                   verbose_name=_("default questions "
                                                                  "status"))
    class Meta:
        abstract = True


class Project(ProjectDefaults, models.Model):
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
    tags = PickledObjectField(null=False, blank=True, verbose_name=_("tags"))
    site = models.ForeignKey("base.Site", related_name="projects", null=True, default=None)

    notifiable_fields = [
        "name",
        "total_milestones",
        "total_story_points",
        # This realy should be in this list?
        # "default_points",
        # "default_us_status",
        # "default_task_status",
        # "default_priority",
        # "default_severity",
        # "default_issue_status",
        # "default_issue_type",
        # "default_question_status",
        "description"
    ]

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projects"
        ordering = ["name"]
        permissions = (
            ("view_project", "Can view project"),
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Project {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super().save(*args, **kwargs)

    def get_roles(self):
        role_model = get_model("users", "Role")
        return role_model.objects.all()

    def get_users(self):
        user_model = get_user_model()
        members = self.memberships.values_list("user", flat=True)
        return user_model.objects.filter(id__in=list(members))

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
                    rolepoints_model.objects.create(role=role, user_story=us,
                                                    points=null_points_value)

        # Now remove rolepoints associated with not existing roles.
        rp_query = rolepoints_model.objects.filter(user_story__in=self.user_stories.all())
        rp_query = rp_query.exclude(role__id__in=roles.values_list("id", flat=True))
        rp_query.delete()

    def _get_user_stories_points(self, user_stories):
        role_points = [us.role_points.all() for us in user_stories]
        flat_role_points = itertools.chain(*role_points)
        flat_role_dicts = map(lambda x: {x.role_id: x.points.value if x.points.value else 0}, flat_role_points)
        return dict_sum(*flat_role_dicts)

    def _get_points_increment(self, client_requirement, team_requirement):
        user_stories = UserStory.objects.none()
        last_milestones = self.milestones.order_by('-estimated_finish')
        last_milestone = last_milestones[0] if last_milestones else None
        user_stories = UserStory.objects.filter(
            created_date__gte=last_milestone.estimated_finish if last_milestones else None,
            project_id=self.id,
            client_requirement=client_requirement,
            team_requirement=team_requirement
        )
        return self._get_user_stories_points(user_stories)

    @property
    def future_team_increment(self):
        team_increment = self._get_points_increment(False, True)
        shared_increment = {key: value/2 for key, value in self.future_shared_increment.items()}
        return dict_sum(team_increment, shared_increment)

    @property
    def future_client_increment(self):
        client_increment = self._get_points_increment(True, False)
        shared_increment = {key: value/2 for key, value in self.future_shared_increment.items()}
        return dict_sum(client_increment, shared_increment)

    @property
    def future_shared_increment(self):
        return self._get_points_increment(True, True)

    @property
    def closed_points(self):
        return dict_sum(*[ml.closed_points for ml in self.milestones.all()])

    @property
    def defined_points(self):
        return self._get_user_stories_points(self.user_stories.all())

    @property
    def assigned_points(self):
        return self._get_user_stories_points(self.user_stories.filter(milestone__isnull=False))


def get_attachment_file_path(instance, filename):
    return "attachment-files/{project}/{model}/{filename}".format(
        project=instance.project.slug,
        model=instance.content_type.model,
        filename=filename
    )


class Attachment(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                              related_name="change_attachments",
                              verbose_name=_("owner"))
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
                                     upload_to=get_attachment_file_path,
                                     verbose_name=_("attached file"))

    class Meta:
        verbose_name = "attachment"
        verbose_name_plural = "attachments"
        ordering = ["project", "created_date"]
        permissions = (
            ("view_attachment", "Can view attachment"),
        )

    def __str__(self):
        return "Attachment: {}".format(self.id)


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
        verbose_name = "user story status"
        verbose_name_plural = "user story statuses"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_userstorystatus", "Can view user story status"),
        )

    def __str__(self):
        return self.name


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
        verbose_name = "points"
        verbose_name_plural = "points"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_points", "Can view points"),
        )

    def __str__(self):
        return self.name


# Tasks common models

class TaskStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="task_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = "task status"
        verbose_name_plural = "task statuses"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_taskstatus", "Can view task status"),
        )

    def __str__(self):
        return self.name


# Issue common Models

class Priority(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="priorities", verbose_name=_("project"))

    class Meta:
        verbose_name = "priority"
        verbose_name_plural = "priorities"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_priority", "Can view priority"),
        )

    def __str__(self):
        return self.name


class Severity(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="severities", verbose_name=_("project"))

    class Meta:
        verbose_name = "severity"
        verbose_name_plural = "severities"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_severity", "Can view severity"),
        )

    def __str__(self):
        return self.name


class IssueStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="issue_statuses", verbose_name=_("project"))

    class Meta:
        verbose_name = "issue status"
        verbose_name_plural = "issue statuses"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_issuestatus", "Can view issue status"),
        )

    def __str__(self):
        return self.name


class IssueType(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="issue_types", verbose_name=_("project"))

    class Meta:
        verbose_name = "issue type"
        verbose_name_plural = "issue types"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_issuetype", "Can view issue type"),
        )

    def __str__(self):
        return self.name


# Questions common models

class QuestionStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    project = models.ForeignKey("Project", null=False, blank=False,
                                related_name="question_status",
                                verbose_name=_("project"))

    class Meta:
        verbose_name = "question status"
        verbose_name_plural = "question statuses"
        ordering = ["project", "order", "name"]
        unique_together = ("project", "name")
        permissions = (
            ("view_questionstatus", "Can view question status"),
        )

    def __str__(self):
        return self.name


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Project)
reversion.register(Attachment)


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
    Populate new project dependen default data
    """
    if not created:
        return

    # USs
    for order, name, value, is_default in choices.POINTS_CHOICES:
        obj = Points.objects.create(project=instance, name=name, order=order, value=value)
        if is_default:
            instance.default_points = obj

    for order, name, is_closed, is_default in choices.US_STATUSES:
        obj = UserStoryStatus.objects.create(name=name, order=order,
                                             is_closed=is_closed, project=instance)
        if is_default:
            instance.default_us_status = obj

    # Tasks
    for order, name, is_closed, is_default, color in choices.TASK_STATUSES:
        obj = TaskStatus.objects.create(name=name, order=order, color=color,
                                        is_closed=is_closed, project=instance)
        if is_default:
            instance.default_task_status = obj

    # Issues
    for order, name, color, is_default in choices.PRIORITY_CHOICES:
        obj = Priority.objects.create(project=instance, name=name, order=order, color=color)
        if is_default:
            instance.default_priority = obj

    for order, name, color, is_default in choices.SEVERITY_CHOICES:
        obj = Severity.objects.create(project=instance, name=name, order=order, color=color)
        if is_default:
            instance.default_severity = obj

    for order, name, is_closed, color, is_default in choices.ISSUE_STATUSES:
        obj = IssueStatus.objects.create(name=name, order=order,
                                         is_closed=is_closed, project=instance, color=color)
        if is_default:
            instance.default_issue_status = obj

    for order, name, color, is_default in choices.ISSUE_TYPES:
        obj = IssueType.objects.create(project=instance, name=name, order=order, color=color)
        if is_default:
            instance.default_issue_type = obj

    # Questions
    for order, name, is_closed, color, is_default in choices.QUESTION_STATUS:
        obj = QuestionStatus.objects.create(name=name, order=order,
                                            is_closed=is_closed, project=instance, color=color)
        if is_default:
            instance.default_question_status = obj

    instance.save()
