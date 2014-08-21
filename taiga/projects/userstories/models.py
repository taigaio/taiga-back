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
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from taiga.base.tags import TaggedMixin
from taiga.base.utils.slug import ref_uniquely
from taiga.projects.notifications import WatchedModelMixin
from taiga.projects.occ import OCCModelMixin
from taiga.projects.mixins.blocked import BlockedMixin
from taiga.projects.services.tags_colors import update_project_tags_colors_handler, remove_unused_tags


class RolePoints(models.Model):
    user_story = models.ForeignKey("UserStory", null=False, blank=False,
                                   related_name="role_points",
                                   verbose_name=_("user story"))
    role = models.ForeignKey("users.Role", null=False, blank=False,
                             related_name="role_points",
                             verbose_name=_("role"))
    points = models.ForeignKey("projects.Points", null=False, blank=False,
                               related_name="role_points",
                               verbose_name=_("points"))

    class Meta:
        verbose_name = "role points"
        verbose_name_plural = "role points"
        unique_together = ("user_story", "role")
        ordering = ["user_story", "role"]
        permissions = (
            ("view_rolepoints", "Can view role points"),
        )

    def __str__(self):
        return "{}: {}".format(self.role.name, self.points.name)


class UserStory(OCCModelMixin, WatchedModelMixin, BlockedMixin, TaggedMixin, models.Model):

    ref = models.BigIntegerField(db_index=True, null=True, blank=True, default=None,
                                 verbose_name=_("ref"))
    milestone = models.ForeignKey("milestones.Milestone", null=True, blank=True,
                                  default=None, related_name="user_stories",
                                  on_delete=models.SET_NULL, verbose_name=_("milestone"))
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="user_stories", verbose_name=_("project"))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_user_stories", verbose_name=_("owner"),
                              on_delete=models.SET_NULL)
    status = models.ForeignKey("projects.UserStoryStatus", null=True, blank=True,
                               related_name="user_stories", verbose_name=_("status"),
                               on_delete=models.SET_NULL)
    is_closed = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False, null=False, blank=True,
                                      verbose_name=_("archived"))
    points = models.ManyToManyField("projects.Points", null=False, blank=False,
                                    related_name="userstories", through="RolePoints",
                                    verbose_name=_("points"))
    order = models.PositiveSmallIntegerField(null=False, blank=False, default=100,
                                             verbose_name=_("order"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    finish_date = models.DateTimeField(null=True, blank=True,
                                       verbose_name=_("finish date"))
    subject = models.TextField(null=False, blank=False,
                               verbose_name=_("subject"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                    default=None, related_name="userstories_assigned_to_me",
                                    verbose_name=_("assigned to"))
    client_requirement = models.BooleanField(default=False, null=False, blank=True,
                                             verbose_name=_("is client requirement"))
    team_requirement = models.BooleanField(default=False, null=False, blank=True,
                                           verbose_name=_("is team requirement"))
    attachments = generic.GenericRelation("attachments.Attachment")
    generated_from_issue = models.ForeignKey("issues.Issue", null=True, blank=True,
                                             related_name="generated_user_stories",
                                             verbose_name=_("generated from issue"))
    _importing = None

    class Meta:
        verbose_name = "user story"
        verbose_name_plural = "user stories"
        ordering = ["project", "order", "ref"]
        #unique_together = ("ref", "project")
        permissions = (
            ("view_userstory", "Can view user story"),
        )

    def save(self, *args, **kwargs):
        if not self._importing:
            self.modified_date = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return "({1}) {0}".format(self.ref, self.subject)

    def __repr__(self):
        return "<UserStory %s>" % (self.id)

    def get_role_points(self):
        return self.role_points

    def get_total_points(self):
        total = 0.0
        for rp in self.role_points.select_related("points"):
            if rp.points.value:
                total += rp.points.value

        return total

    def get_notifiable_assigned_to_display(self, value):
        if not value:
            return _("Unassigned")
        return value.get_full_name()

    def get_notifiable_tags_display(self, value):
        if type(value) is list:
            return ", ".join(value)
        return value

    def get_notifiable_points_display(self, value):
        if isinstance(value, models.manager.Manager):
            return ", ".join(["{}: {}".format(rp.role.name, rp.points.name)
                              for rp in self.role_points.all().order_by("role")])
        return None


@receiver(models.signals.post_save, sender=UserStory,
          dispatch_uid="user_story_create_role_points_handler")
def us_create_role_points_handler(sender, instance, **kwargs):
    instance.project.update_role_points(user_stories=[instance])


@receiver(models.signals.post_save, sender=UserStory,
          dispatch_uid="user_story_tasks_reassignation")
def us_task_reassignation(sender, instance, created, **kwargs):
    if not created:
        instance.tasks.update(milestone=instance.milestone)


@receiver(models.signals.pre_save, sender=UserStory, dispatch_uid="us-tags-normalization")
def us_tags_normalization(sender, instance, **kwargs):
    if isinstance(instance.tags, (list, tuple)):
        instance.tags = list(map(str.lower, instance.tags))

@receiver(models.signals.post_save, sender=UserStory,
          dispatch_uid="user_story_on_status_change")
def us_close_open_on_status_change(sender, instance, **kwargs):
    from taiga.projects.userstories import services as service

    if service.calculate_userstory_is_closed(instance):
        service.close_userstory(instance)
    else:
        service.open_userstory(instance)


@receiver(models.signals.post_save, sender=UserStory, dispatch_uid="user_story_update_project_colors")
def us_update_project_tags(sender, instance, **kwargs):
    update_project_tags_colors_handler(instance)


@receiver(models.signals.post_delete, sender=UserStory, dispatch_uid="user_story_update_project_colors_on_delete")
def us_update_project_tags_on_delete(sender, instance, **kwargs):
    remove_unused_tags(instance.project)
    instance.project.save()
