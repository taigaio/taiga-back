# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from importlib import import_module

import random
import uuid
import re

from django.apps import apps
from django.apps.config import MODELS_MODULE_NAME
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.core.exceptions import AppRegistryNotReady
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from taiga.base.db.models.fields import JSONField
from django_pglocks import advisory_lock

from taiga.base.utils.colors import generate_random_hex_color
from taiga.base.utils.slug import slugify_uniquely
from taiga.base.utils.files import get_file_path
from taiga.base.utils.time import timestamp_ms
from taiga.permissions.choices import MEMBERS_PERMISSIONS
from taiga.projects.choices import BLOCKED_BY_OWNER_LEAVING
from taiga.projects.notifications.choices import NotifyLevel

from . import services


def get_user_model_safe():
    """
    Fetches the user model using the app registry.
    This doesn't require that an app with the given app label exists,
    which makes it safe to call when the registry is being populated.
    All other methods to access models might raise an exception about the
    registry not being ready yet.
    Raises LookupError if model isn't found.

    Based on: https://github.com/django-oscar/django-oscar/blob/1.0/oscar/core/loading.py#L310-L340
    Ongoing Django issue: https://code.djangoproject.com/ticket/22872
    """
    user_app, user_model = settings.AUTH_USER_MODEL.split('.')

    try:
        return apps.get_model(user_app, user_model)
    except AppRegistryNotReady:
        if apps.apps_ready and not apps.models_ready:
            # If this function is called while `apps.populate()` is
            # loading models, ensure that the module that defines the
            # target model has been imported and try looking the model up
            # in the app registry. This effectively emulates
            # `from path.to.app.models import Model` where we use
            # `Model = get_model('app', 'Model')` instead.
            app_config = apps.get_app_config(user_app)
            # `app_config.import_models()` cannot be used here because it
            # would interfere with `apps.populate()`.
            import_module('%s.%s' % (app_config.name, MODELS_MODULE_NAME))
            # In order to account for case-insensitivity of model_name,
            # look up the model through a private API of the app registry.
            return apps.get_registered_model(user_app, user_model)
        else:
            # This must be a different case (e.g. the model really doesn't
            # exist). We just re-raise the exception.
            raise


def get_user_file_path(instance, filename):
    return get_file_path(instance, filename, "user")


class PermissionsMixin(models.Model):
    """
    A mixin class that adds the fields and methods necessary to support
    Django"s Permission model using the ModelBackend.
    """
    is_superuser = models.BooleanField(_("superuser status"), default=False,
        help_text=_("Designates that this user has all permissions without "
                    "explicitly assigning them."))

    class Meta:
        abstract = True

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser


def get_default_uuid():
    return uuid.uuid4().hex


class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.CharField(max_length=32, editable=False, null=False,
                            blank=False, unique=True, default=get_default_uuid)
    username = models.CharField(_("username"), max_length=255, unique=True,
        help_text=_("Required. 30 characters or fewer. Letters, numbers and "
                    "/./-/_ characters"),
        validators=[
            validators.RegexValidator(re.compile(r"^[\w.-]+$"), _("Enter a valid username."), "invalid")
        ])
    email = models.EmailField(_("email address"), max_length=255, null=False, blank=False, unique=True)
    is_active = models.BooleanField(_("active"), default=True,
        help_text=_("Designates whether this user should be treated as "
                    "active. Unselect this instead of deleting accounts."))
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )

    full_name = models.CharField(_("full name"), max_length=256, blank=True)
    color = models.CharField(max_length=9, null=False, blank=True, default=generate_random_hex_color,
                             verbose_name=_("color"))
    bio = models.TextField(null=False, blank=True, default="", verbose_name=_("biography"))
    photo = models.FileField(upload_to=get_user_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("photo"))
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    date_cancelled = models.DateTimeField(_("date cancelled"), null=True, blank=True, default=None)
    accepted_terms = models.BooleanField(_("accepted terms"), default=True)
    read_new_terms = models.BooleanField(_("new terms read"), default=False)
    lang = models.CharField(max_length=20, null=True, blank=True, default="",
                            verbose_name=_("default language"))
    theme = models.CharField(max_length=100, null=True, blank=True, default="",
                            verbose_name=_("default theme"))
    timezone = models.CharField(max_length=20, null=True, blank=True, default="",
                                verbose_name=_("default timezone"))
    colorize_tags = models.BooleanField(null=False, blank=True, default=False,
                                        verbose_name=_("colorize tags"))
    token = models.CharField(max_length=200, null=True, blank=True, default=None,
                             verbose_name=_("token"))

    email_token = models.CharField(max_length=200, null=True, blank=True, default=None,
                         verbose_name=_("email token"))

    new_email = models.EmailField(_("new email address"), null=True, blank=True)
    verified_email = models.BooleanField(null=False, blank=False, default=True)
    is_system = models.BooleanField(null=False, blank=False, default=False)


    max_private_projects = models.IntegerField(null=True, blank=True,
                                               default=settings.MAX_PRIVATE_PROJECTS_PER_USER,
                                               verbose_name=_("max number of owned private projects"))
    max_public_projects = models.IntegerField(null=True, blank=True,
                                              default=settings.MAX_PUBLIC_PROJECTS_PER_USER,
                                              verbose_name=_("max number of owned public projects"))
    max_memberships_private_projects = models.IntegerField(null=True, blank=True,
                                                           default=settings.MAX_MEMBERSHIPS_PRIVATE_PROJECTS,
                                                           verbose_name=_("max number of memberships of "
                                                                          "different users for all owned "
                                                                          "private project"))
    max_memberships_public_projects = models.IntegerField(null=True, blank=True,
                                                          default=settings.MAX_MEMBERSHIPS_PUBLIC_PROJECTS,
                                                          verbose_name=_("max number of memberships of "
                                                                         "different users for all owned "
                                                                         "public project"))

    _cached_memberships = None
    _cached_liked_ids = None
    _cached_watched_ids = None
    _cached_notify_levels = None

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name()

    def _fill_cached_memberships(self):
        self._cached_memberships = {}
        qs = self.memberships.select_related("user", "project", "role")
        for membership in qs.all():
            self._cached_memberships[membership.project.id] = membership

    @property
    def cached_memberships(self):
        if self._cached_memberships is None:
            self._fill_cached_memberships()

        return self._cached_memberships.values()

    def cached_membership_for_project(self, project):
        if self._cached_memberships is None:
            self._fill_cached_memberships()

        return self._cached_memberships.get(project.id, None)

    def is_fan(self, obj):
        if self._cached_liked_ids is None:
            self._cached_liked_ids = set()
            for like in self.likes.select_related("content_type").all():
                like_id = "{}-{}".format(like.content_type.id, like.object_id)
                self._cached_liked_ids.add(like_id)

        obj_type = ContentType.objects.get_for_model(obj)
        obj_id = "{}-{}".format(obj_type.id, obj.id)
        return obj_id in self._cached_liked_ids

    def is_watcher(self, obj):
        if self._cached_watched_ids is None:
            self._cached_watched_ids = set()
            for watched in self.watched.select_related("content_type").all():
                watched_id = "{}-{}".format(watched.content_type.id, watched.object_id)
                self._cached_watched_ids.add(watched_id)

            notify_policies = self.notify_policies.select_related("project")\
                .exclude(notify_level=NotifyLevel.none)

            for notify_policy in notify_policies:
                obj_type = ContentType.objects.get_for_model(notify_policy.project)
                watched_id = "{}-{}".format(obj_type.id, notify_policy.project.id)
                self._cached_watched_ids.add(watched_id)

        obj_type = ContentType.objects.get_for_model(obj)
        obj_id = "{}-{}".format(obj_type.id, obj.id)
        return obj_id in self._cached_watched_ids

    def get_notify_level(self, project):
        if self._cached_notify_levels is None:
            self._cached_notify_levels = {}
            for notify_policy in self.notify_policies.select_related("project"):
                self._cached_notify_levels[notify_policy.project.id] = notify_policy.notify_level

        return self._cached_notify_levels.get(project.id, None)

    def get_short_name(self):
        "Returns the short name for the user."
        return self.username

    def get_full_name(self):
        return self.full_name or self.username or self.email

    def contacts_visible_by_user(self, user):
        qs = User.objects.filter(is_active=True)
        project_ids = services.get_visible_project_ids(self, user)
        qs = qs.filter(memberships__project_id__in=project_ids)
        qs = qs.exclude(id=self.id)
        return qs

    def cancel(self):
        with advisory_lock("delete-user"):
            deleted_user_prefix = "deleted-user-{}".format(timestamp_ms())
            self.username = slugify_uniquely(deleted_user_prefix, User, slugfield="username")
            self.email = "{}@taiga.io".format(self.username)
            self.is_active = False
            self.full_name = "Deleted user"
            self.color = ""
            self.bio = ""
            self.lang = ""
            self.theme = ""
            self.timezone = ""
            self.colorize_tags = True
            self.token = None
            self.set_unusable_password()
            self.photo = None
            self.date_cancelled = timezone.now()
            self.new_email = "{}@taiga.io".format(self.username)
            self.email_token = None
            self.save()
        self.auth_data.all().delete()

        # Blocking all owned projects
        self.owned_projects.update(blocked_code=BLOCKED_BY_OWNER_LEAVING)

        # Remove all memberships
        self.memberships.all().delete()


class Role(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, null=False, blank=True,
                            verbose_name=_("slug"))
    permissions = ArrayField(models.TextField(null=False, blank=False, choices=MEMBERS_PERMISSIONS),
                             null=True, blank=True, default=list, verbose_name=_("permissions"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    # null=True is for make work django 1.7 migrations. project
    # field causes some circular dependencies, and due to this
    # it can not be serialized in one transactional migration.
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=False,
        related_name="roles",
        verbose_name=_("project"),
        on_delete=models.CASCADE,
    )
    computable = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "role"
        verbose_name_plural = "roles"
        ordering = ["order", "slug"]
        unique_together = (("slug", "project"),)

    def __str__(self):
        return self.name


class AuthData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="auth_data", on_delete=models.CASCADE)
    key = models.SlugField(max_length=50)
    value = models.CharField(max_length=300)
    extra = JSONField()

    class Meta:
        unique_together = ["key", "value"]


# On Role object is changed, update all membership
# related to current role.
@receiver(models.signals.post_save, sender=Role,
          dispatch_uid="role_post_save")
def role_post_save(sender, instance, created, **kwargs):
    # ignore if object is just created
    if created:
        return

    instance.project.update_role_points()
