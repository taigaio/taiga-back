# -*- coding: utf-8 -*-

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import UserManager, AbstractUser

from greenmine.base.notifications.models import WatcherMixin


class User(AbstractUser, WatcherMixin):
    color = models.CharField(max_length=9, null=False, blank=True, default="#669933",
                             verbose_name=_("color"))
    description = models.TextField(null=False, blank=True,
                                   verbose_name=_("description"))
    photo = models.FileField(upload_to="files/msg", max_length=500, null=True, blank=True,
                             verbose_name=_("photo"))
    default_language = models.CharField(max_length=20, null=False, blank=True, default="",
                                        verbose_name=_("default language"))
    default_timezone = models.CharField(max_length=20, null=False, blank=True, default="",
                                        verbose_name=_("default timezone"))
    token = models.CharField(max_length=200, null=True, blank=True, default=None,
                             verbose_name=_("token"))
    colorize_tags = models.BooleanField(null=False, blank=True, default=False,
                                        verbose_name=_("colorize tags"))
    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["username"]
        permissions = (
            ("view_user", "Can view user"),
        )

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return super().get_full_name() or self.username or self.email


class Role(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                            verbose_name=_("slug"))
    permissions = models.ManyToManyField("auth.Permission", related_name="roles",
                                         verbose_name=_("permissions"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    computable = models.BooleanField(default=True)

    class Meta:
        verbose_name = "role"
        verbose_name_plural = "roles"
        ordering = ["order", "slug"]
        permissions = (
            ("view_role", "Can view role"),
        )

    def __str__(self):
        return self.name


# On Role object is changed, update all membership
# related to current role.
@receiver(models.signals.post_save, sender=Role,
          dispatch_uid="role_post_save")
def role_post_save(sender, instance, created, **kwargs):
    # ignore if object is just created
    if created:
        return

    unique_projects = set(map(lambda x: x.project, instance.memberships.all()))
    for project in unique_projects:
        project.update_role_points()

