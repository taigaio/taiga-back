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

import itertools

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.db.models.loading import get_model
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django_pgjson.fields import JsonField
from djorm_pgarray.fields import TextArrayField
from taiga.permissions.permissions import ANON_PERMISSIONS, USER_PERMISSIONS

from taiga.base.tags import TaggedMixin
from taiga.users.models import Role
from taiga.base.utils.slug import slugify_uniquely
from taiga.base.utils.dicts import dict_sum
from taiga.base.utils.sequence import arithmetic_progression
from taiga.projects.notifications.services import create_notify_policy_if_not_exists

from . import choices

# FIXME: this should to be on choices module (?)
VIDEOCONFERENCES_CHOICES = (
    ('appear-in', 'AppearIn'),
    ('talky', 'Talky'),
)


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
    is_owner = models.BooleanField(default=False, null=False, blank=False)

    # Invitation metadata
    email = models.EmailField(max_length=255, default=None, null=True, blank=True,
                              verbose_name=_("email"))
    created_at = models.DateTimeField(default=timezone.now,
                                      verbose_name=_("creado el"))
    token = models.CharField(max_length=60, blank=True, null=True, default=None,
                             verbose_name=_("token"))
    invited_by_id = models.IntegerField(null=True, blank=True)

    def clean(self):
        # TODO: Review and do it more robust
        memberships = Membership.objects.filter(user=self.user, project=self.project)
        if self.user and memberships.count() > 0 and memberships[0].id != self.id:
            raise ValidationError(_('The user is already member of the project'))

    class Meta:
        verbose_name = "membership"
        verbose_name_plural = "membershipss"
        unique_together = ("user", "project",)
        ordering = ["project", "user__full_name", "user__username", "user__email", "email"]
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

    class Meta:
        abstract = True


class Project(ProjectDefaults, TaggedMixin, models.Model):
    name = models.CharField(max_length=250, unique=True, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                            verbose_name=_("slug"))
    description = models.TextField(null=False, blank=False,
                                   verbose_name=_("description"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                              related_name="owned_projects", verbose_name=_("owner"))
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="projects",
                                     through="Membership", verbose_name=_("members"))
    total_milestones = models.IntegerField(default=0, null=True, blank=True,
                                           verbose_name=_("total of milestones"))
    total_story_points = models.FloatField(default=0, verbose_name=_("total story points"))

    is_backlog_activated = models.BooleanField(default=True, null=False, blank=True,
                                               verbose_name=_("active backlog panel"))
    is_kanban_activated = models.BooleanField(default=False, null=False, blank=True,
                                              verbose_name=_("active kanban panel"))
    is_wiki_activated = models.BooleanField(default=True, null=False, blank=True,
                                            verbose_name=_("active wiki panel"))
    is_issues_activated = models.BooleanField(default=True, null=False, blank=True,
                                              verbose_name=_("active issues panel"))
    videoconferences = models.CharField(max_length=250, null=True, blank=True,
                                        choices=choices.VIDEOCONFERENCES_CHOICES,
                                        verbose_name=_("videoconference system"))
    videoconferences_salt = models.CharField(max_length=250, null=True, blank=True,
                                             verbose_name=_("videoconference room salt"))

    creation_template = models.ForeignKey("projects.ProjectTemplate",
                                          related_name="projects", null=True,
                                          blank=True, default=None,
                                          verbose_name=_("creation template"))
    anon_permissions = TextArrayField(blank=True, null=True,
                                      default=[],
                                      verbose_name=_("anonymous permissions"),
                                      choices=ANON_PERMISSIONS)
    public_permissions = TextArrayField(blank=True, null=True,
                                        default=[],
                                        verbose_name=_("user permissions"),
                                        choices=USER_PERMISSIONS)
    is_private = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is private"))

    tags_colors = TextArrayField(dimension=2, null=False, blank=True, verbose_name=_("tags colors"), default=[])
    _importing = None

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
        if not self._importing:
            self.modified_date = timezone.now()

        if not self.slug:
            base_slug = slugify_uniquely(self.name, self.__class__)
            slug = base_slug
            for i in arithmetic_progression():
                if not type(self).objects.filter(slug=slug).exists() or i > 100:
                    break
                slug = "{}-{}".format(base_slug, i)
            self.slug = slug

        if not self.videoconferences:
            self.videoconferences_salt = None

        super().save(*args, **kwargs)

    def get_roles(self):
        return self.roles.all()

    def get_users(self):
        user_model = get_user_model()
        members = self.memberships.values_list("user", flat=True)
        return user_model.objects.filter(id__in=list(members))

    def update_role_points(self, user_stories=None):
        RolePoints = get_model("userstories", "RolePoints")
        Role = get_model("users", "Role")

        # Get all available roles on this project
        roles = self.get_roles().filter(computable=True)
        if roles.count() == 0:
            return

        # Get point instance that represent a null/undefined
        try:
            null_points_value = self.points.get(value=None)
        except Points.DoesNotExist:
            null_points_value = None

        # Iter over all project user stories and create
        # role point instance for new created roles.
        if user_stories is None:
            user_stories = self.user_stories.all()

        for story in user_stories:
            story_related_roles = Role.objects.filter(role_points__in=story.role_points.all())\
                                              .distinct()
            new_roles = roles.exclude(id__in=story_related_roles)
            new_rolepoints = [RolePoints(role=role, user_story=story, points=null_points_value)
                              for role in new_roles]
            RolePoints.objects.bulk_create(new_rolepoints)

        # Now remove rolepoints associated with not existing roles.
        rp_query = RolePoints.objects.filter(user_story__in=self.user_stories.all())
        rp_query = rp_query.exclude(role__id__in=roles.values_list("id", flat=True))
        rp_query.delete()

    def _get_user_stories_points(self, user_stories):
        role_points = [us.role_points.all() for us in user_stories]
        flat_role_points = itertools.chain(*role_points)
        flat_role_dicts = map(lambda x: {x.role_id: x.points.value if x.points.value else 0}, flat_role_points)
        return dict_sum(*flat_role_dicts)

    def _get_points_increment(self, client_requirement, team_requirement):
        userstory_model = get_model("userstories", "UserStory")
        user_stories = userstory_model.objects.none()
        last_milestones = self.milestones.order_by('-estimated_finish')
        last_milestone = last_milestones[0] if last_milestones else None
        if last_milestone:
            user_stories = userstory_model.objects.filter(
                created_date__gte=last_milestone.estimated_finish,
                project_id=self.id,
                client_requirement=client_requirement,
                team_requirement=team_requirement
            ).prefetch_related('role_points', 'role_points__points')
        else:
            user_stories = userstory_model.objects.filter(
                project_id=self.id,
                client_requirement=client_requirement,
                team_requirement=team_requirement
            ).prefetch_related('role_points', 'role_points__points')
        return self._get_user_stories_points(user_stories)

    @property
    def future_team_increment(self):
        team_increment = self._get_points_increment(False, True)
        shared_increment = {key: value / 2 for key, value in self.future_shared_increment.items()}
        return dict_sum(team_increment, shared_increment)

    @property
    def future_client_increment(self):
        client_increment = self._get_points_increment(True, False)
        shared_increment = {key: value / 2 for key, value in self.future_shared_increment.items()}
        return dict_sum(client_increment, shared_increment)

    @property
    def future_shared_increment(self):
        return self._get_points_increment(True, True)

    @property
    def closed_points(self):
        return self._get_user_stories_points(self.user_stories.filter(is_closed=True).prefetch_related('role_points', 'role_points__points'))

    @property
    def defined_points(self):
        return self._get_user_stories_points(self.user_stories.all().prefetch_related('role_points', 'role_points__points'))

    @property
    def assigned_points(self):
        return self._get_user_stories_points(self.user_stories.filter(milestone__isnull=False).prefetch_related('role_points', 'role_points__points'))


# User Stories common Models
class UserStoryStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("name"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    is_closed = models.BooleanField(default=False, null=False, blank=True,
                                    verbose_name=_("is closed"))
    color = models.CharField(max_length=20, null=False, blank=False, default="#999999",
                             verbose_name=_("color"))
    wip_limit = models.IntegerField(null=True, blank=True, default=None,
                                    verbose_name=_("work in progress limit"))
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


class ProjectTemplate(models.Model):
    name = models.CharField(max_length=250, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, null=False, blank=True,
                            verbose_name=_("slug"), unique=True)
    description = models.TextField(null=False, blank=False,
                                   verbose_name=_("description"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    default_owner_role = models.CharField(max_length=50, null=False,
                                          blank=False,
                                          verbose_name=_("default owner's role"))

    is_backlog_activated = models.BooleanField(default=True, null=False, blank=True,
                                               verbose_name=_("active backlog panel"))
    is_kanban_activated = models.BooleanField(default=False, null=False, blank=True,
                                              verbose_name=_("active kanban panel"))
    is_wiki_activated = models.BooleanField(default=True, null=False, blank=True,
                                            verbose_name=_("active wiki panel"))
    is_issues_activated = models.BooleanField(default=True, null=False, blank=True,
                                              verbose_name=_("active issues panel"))
    videoconferences = models.CharField(max_length=250, null=True, blank=True,
                                        choices=choices.VIDEOCONFERENCES_CHOICES,
                                        verbose_name=_("videoconference system"))
    videoconferences_salt = models.CharField(max_length=250, null=True, blank=True,
                                             verbose_name=_("videoconference room salt"))

    default_options = JsonField(null=True, blank=True, verbose_name=_("default options"))
    us_statuses = JsonField(null=True, blank=True, verbose_name=_("us statuses"))
    points = JsonField(null=True, blank=True, verbose_name=_("points"))
    task_statuses = JsonField(null=True, blank=True, verbose_name=_("task statuses"))
    issue_statuses = JsonField(null=True, blank=True, verbose_name=_("issue statuses"))
    issue_types = JsonField(null=True, blank=True, verbose_name=_("issue types"))
    priorities = JsonField(null=True, blank=True, verbose_name=_("priorities"))
    severities = JsonField(null=True, blank=True, verbose_name=_("severities"))
    roles = JsonField(null=True, blank=True, verbose_name=_("roles"))
    _importing = None

    class Meta:
        verbose_name = "project template"
        verbose_name_plural = "project templates"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Project Template {0}>".format(self.slug)

    def save(self, *args, **kwargs):
        if not self._importing:
            self.modified_date = timezone.now()
        super().save(*args, **kwargs)

    def load_data_from_project(self, project):
        self.is_backlog_activated = project.is_backlog_activated
        self.is_kanban_activated = project.is_kanban_activated
        self.is_wiki_activated = project.is_wiki_activated
        self.is_issues_activated = project.is_issues_activated
        self.videoconferences = project.videoconferences
        self.videoconferences_salt = project.videoconferences_salt

        self.default_options = {
            "points": getattr(project.default_points, "name", None),
            "us_status": getattr(project.default_us_status, "name", None),
            "task_status": getattr(project.default_task_status, "name", None),
            "issue_status": getattr(project.default_issue_status, "name", None),
            "issue_type": getattr(project.default_issue_type, "name", None),
            "priority": getattr(project.default_priority, "name", None),
            "severity": getattr(project.default_severity, "name", None)
        }

        self.us_statuses = []
        for us_status in project.us_statuses.all():
            self.us_statuses.append({
                "name": us_status.name,
                "is_closed": us_status.is_closed,
                "color": us_status.color,
                "wip_limit": us_status.wip_limit,
                "order": us_status.order,
            })

        self.points = []
        for us_point in project.points.all():
            self.points.append({
                "name": us_point.name,
                "value": us_point.value,
                "order": us_point.order,
            })

        self.task_statuses = []
        for task_status in project.task_statuses.all():
            self.task_statuses.append({
                "name": task_status.name,
                "is_closed": task_status.is_closed,
                "color": task_status.color,
                "order": task_status.order,
            })

        self.issue_statuses = []
        for issue_status in project.issue_statuses.all():
            self.issue_statuses.append({
                "name": issue_status.name,
                "is_closed": issue_status.is_closed,
                "color": issue_status.color,
                "order": issue_status.order,
            })

        self.issue_types = []
        for issue_type in project.issue_types.all():
            self.issue_types.append({
                "name": issue_type.name,
                "color": issue_type.color,
                "order": issue_type.order,
            })

        self.priorities = []
        for priority in project.priorities.all():
            self.priorities.append({
                "name": priority.name,
                "color": priority.color,
                "order": priority.order,
            })

        self.severities = []
        for severity in project.severities.all():
            self.severities.append({
                "name": severity.name,
                "color": severity.color,
                "order": severity.order,
            })

        self.roles = []
        for role in project.roles.all():
            self.roles.append({
                "name": role.name,
                "slug": role.slug,
                "permissions": role.permissions,
                "order": role.order,
                "computable": role.computable
            })

        try:
            owner_membership = Membership.objects.get(project=project, user=project.owner)
            self.default_owner_role = owner_membership.role.slug
        except Membership.DoesNotExist:
            self.default_owner_role = self.roles[0].get("slug", None)

    def apply_to_project(self, project):
        if project.id is None:
            raise Exception("Project need an id (must be a saved project)")

        project.creation_template = self
        project.is_backlog_activated = self.is_backlog_activated
        project.is_kanban_activated = self.is_kanban_activated
        project.is_wiki_activated = self.is_wiki_activated
        project.is_issues_activated = self.is_issues_activated
        project.videoconferences = self.videoconferences
        project.videoconferences_salt = self.videoconferences_salt

        for us_status in self.us_statuses:
            UserStoryStatus.objects.create(
                name=us_status["name"],
                is_closed=us_status["is_closed"],
                color=us_status["color"],
                wip_limit=us_status["wip_limit"],
                order=us_status["order"],
                project=project
            )

        for point in self.points:
            Points.objects.create(
                name=point["name"],
                value=point["value"],
                order=point["order"],
                project=project
            )

        for task_status in self.task_statuses:
            TaskStatus.objects.create(
                name=task_status["name"],
                is_closed=task_status["is_closed"],
                color=task_status["color"],
                order=task_status["order"],
                project=project
            )

        for issue_status in self.issue_statuses:
            IssueStatus.objects.create(
                name=issue_status["name"],
                is_closed=issue_status["is_closed"],
                color=issue_status["color"],
                order=issue_status["order"],
                project=project
            )

        for issue_type in self.issue_types:
            IssueType.objects.create(
                name=issue_type["name"],
                color=issue_type["color"],
                order=issue_type["order"],
                project=project
            )

        for priority in self.priorities:
            Priority.objects.create(
                name=priority["name"],
                color=priority["color"],
                order=priority["order"],
                project=project
            )

        for severity in self.severities:
            Severity.objects.create(
                name=severity["name"],
                color=severity["color"],
                order=severity["order"],
                project=project
            )

        for role in self.roles:
            Role.objects.create(
                name=role["name"],
                slug=role["slug"],
                order=role["order"],
                computable=role["computable"],
                project=project,
                permissions=role['permissions']
            )

        if self.points:
            project.default_points = Points.objects.get(name=self.default_options["points"],
                                                        project=project)
        if self.us_statuses:
            project.default_us_status = UserStoryStatus.objects.get(name=self.default_options["us_status"],
                                                                    project=project)

        if self.task_statuses:
            project.default_task_status = TaskStatus.objects.get(name=self.default_options["task_status"],
                                                                 project=project)
        if self.issue_statuses:
            project.default_issue_status = IssueStatus.objects.get(name=self.default_options["issue_status"],
                                                                   project=project)

        if self.issue_types:
            project.default_issue_type = IssueType.objects.get(name=self.default_options["issue_type"],
                                                               project=project)

        if self.priorities:
            project.default_priority = Priority.objects.get(name=self.default_options["priority"], project=project)

        if self.severities:
            project.default_severity = Severity.objects.get(name=self.default_options["severity"], project=project)

        return project


# On membership object is deleted, update role-points relation.
@receiver(signals.pre_delete, sender=Membership, dispatch_uid='membership_pre_delete')
def membership_post_delete(sender, instance, using, **kwargs):
    instance.project.update_role_points()


# On membership object is deleted, update watchers of all objects relation.
@receiver(signals.post_delete, sender=Membership, dispatch_uid='update_watchers_on_membership_post_delete')
def update_watchers_on_membership_post_delete(sender, instance, using, **kwargs):
    models = [get_model("userstories", "UserStory"),
              get_model("tasks", "Task"),
              get_model("issues", "Issue")]

    # `user_id` is used beacuse in some momments
    # instance.user can contain pointer to now
    # removed object from a database.
    for model in models:
        model.watchers.through.objects.filter(user_id=instance.user_id).delete()


# On membership object is deleted, update watchers of all objects relation.
@receiver(signals.post_save, sender=Membership, dispatch_uid='create-notify-policy')
def create_notify_policy(sender, instance, using, **kwargs):
    if instance.user:
        create_notify_policy_if_not_exists(instance.project, instance.user)


@receiver(signals.post_save, sender=Project, dispatch_uid='project_post_save')
def project_post_save(sender, instance, created, **kwargs):
    """
    Populate new project dependen default data
    """
    if not created:
        return

    template = getattr(instance, "creation_template", None)
    if template is None:
        template = ProjectTemplate.objects.get(slug=settings.DEFAULT_PROJECT_TEMPLATE)
    template.apply_to_project(instance)

    instance.save()

    try:
        owner_role = instance.roles.get(slug=template.default_owner_role)
    except Role.DoesNotExist:
        owner_role = instance.roles.first()

    if owner_role:
        Membership.objects.create(user=instance.owner, project=instance, role=owner_role,
                                  is_owner=True, email=instance.owner.email)
