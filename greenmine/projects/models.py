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

    def __unicode__(self):
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


class Project(models.Model, WatchedMixin):
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
    total_milestones = models.IntegerField(default=1, null=True, blank=True,
                                           verbose_name=_("total of milestones"))
    total_story_points = models.FloatField(default=None, null=True, blank=False,
                                           verbose_name=_("total story points"))
    tags = PickledObjectField(null=False, blank=True,
                              verbose_name=_("tags"))

    notifiable_fields = [
        "name",
        "description",
        "owner",
        "members",
        "public",
        "tags",
    ]

    class Meta:
        verbose_name = u"project"
        verbose_name_plural = u"projects"
        ordering = ["name"]
        permissions = (
            ("list_projects", "Can list projects"),
            ("view_project", "Can view project"),
            ("manage_users", "Can manage users"),
        )

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u"<Project {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super(Project, self).save(*args, **kwargs)

    def _get_watchers_by_role(self):
        return {"owner": self.owner}

    @property
    def list_of_milestones(self):
        return [{
            "name": milestone.name,
            "finish_date": milestone.estimated_finish,
            "closed_points": milestone.closed_points,
            "client_increment_points": milestone.client_increment_points,
            "team_increment_points": milestone.team_increment_points
        } for milestone in self.milestones.all().order_by("estimated_start")]

    @property
    def list_roles(self):
        role_model = get_model("users", "Role")
        return role_model.objects.filter(id__in=list(self.memberships.values_list(
                                                                 "role", flat=True)))

    @property
    def list_users(self):
        user_model = get_user_model()
        return user_model.objects.filter(id__in=list(self.memberships.values_list(
                                                                 "user", flat=True)))

    def update_role_points(self):
        roles = self.list_roles
        role_ids = roles.values_list("id", flat=True)
        null_points = self.points.get(value=None)
        for us in self.user_stories.all():
            for role in roles:
                try:
                    sp = us.role_points.get(role=role, user_story=us)
                except RolePoints.DoesNotExist:
                    sp = RolePoints.objects.create(role=role,
                                                   user_story=us,
                                                   points=null_points)

        #Remove unnecesary Role points
        rp_query = RolePoints.objects.filter(user_story__in=self.user_stories.all())
        rp_query = rp_query.exclude(role__id__in=role_ids)
        rp_query.delete()


# Reversion registration (usufull for base.notification and for meke a historical)
reversion.register(Project)

# Signals dispatches
@receiver(models.signals.post_save, sender=Membership,
          dispatch_uid='membership_post_save')
def membership_post_save(sender, instance, created, **kwargs):
    instance.project.update_role_points()


@receiver(models.signals.post_delete, sender=Membership,
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
    for order, name in choices.PRIORITY_CHOICES:
        Priority.objects.create(project=instance, name=name, order=order)

    for order, name in choices.SEVERITY_CHOICES:
        Severity.objects.create(project=instance, name=name, order=order)

    for order, name, value in choices.POINTS_CHOICES:
        Points.objects.create(project=instance, name=name, order=order, value=value)

    for order, name, is_closed in choices.USSTATUSES:
        UserStoryStatus.objects.create(name=name, order=order,
                                       is_closed=is_closed, project=instance)

    for order, name, is_closed, color in choices.TASKSTATUSES:
        TaskStatus.objects.create(name=name, order=order, color=color,
                                  is_closed=is_closed, project=instance)

    for order, name, is_closed in choices.ISSUESTATUSES:
        IssueStatus.objects.create(name=name, order=order,
                                   is_closed=is_closed, project=instance)

    for order, name in choices.ISSUETYPES:
        IssueType.objects.create(project=instance, name=name, order=order)

    for order, name, is_closed in choices.QUESTION_STATUS:
        QuestionStatus.objects.create(name=name, order=order,
                                   is_closed=is_closed, project=instance)
