# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

import hashlib
import os
import os.path as path
import random
import re
import uuid

from unidecode import unidecode

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import UserManager, AbstractBaseUser
from django.core import validators
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.template.defaultfilters import slugify

from django_pgjson.fields import JsonField
from djorm_pgarray.fields import TextArrayField

from taiga.auth.tokens import get_token_for_user
from taiga.base.utils.slug import slugify_uniquely
from taiga.base.utils.iterators import split_by_n
from taiga.permissions.permissions import MEMBERS_PERMISSIONS
from taiga.projects.notifications.choices import NotifyLevel

from easy_thumbnails.files import get_thumbnailer


def generate_random_hex_color():
    return "#{:06x}".format(random.randint(0,0xFFFFFF))


def get_user_file_path(instance, filename):
    basename = path.basename(filename).lower()
    base, ext = path.splitext(basename)
    base = slugify(unidecode(base))
    basename = "".join([base, ext])

    hs = hashlib.sha256()
    hs.update(force_bytes(timezone.now().isoformat()))
    hs.update(os.urandom(1024))

    p1, p2, p3, p4, *p5 = split_by_n(hs.hexdigest(), 1)
    hash_part = path.join(p1, p2, p3, p4, "".join(p5))

    return path.join("user", hash_part, basename)


class PermissionsMixin(models.Model):
    """
    A mixin class that adds the fields and methods necessary to support
    Django's Permission model using the ModelBackend.
    """
    is_superuser = models.BooleanField(_('superuser status'), default=False,
        help_text=_('Designates that this user has all permissions without '
                    'explicitly assigning them.'))

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

    @property
    def is_staff(self):
        return self.is_superuser


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=255, unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, numbers and '
                    '/./-/_ characters'),
        validators=[
            validators.RegexValidator(re.compile('^[\w.-]+$'), _('Enter a valid username.'), 'invalid')
        ])
    email = models.EmailField(_('email address'), max_length=255, blank=True, unique=True)
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))

    full_name = models.CharField(_('full name'), max_length=256, blank=True)
    color = models.CharField(max_length=9, null=False, blank=True, default=generate_random_hex_color,
                             verbose_name=_("color"))
    bio = models.TextField(null=False, blank=True, default="", verbose_name=_("biography"))
    photo = models.FileField(upload_to=get_user_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("photo"))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
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

    new_email = models.EmailField(_('new email address'), null=True, blank=True)

    is_system = models.BooleanField(null=False, blank=False, default=False)
    _cached_memberships = None
    _cached_liked_ids = None
    _cached_watched_ids = None
    _cached_notify_levels = None

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

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

    def _fill_cached_memberships(self):
        self._cached_memberships = {}
        qs = self.memberships.prefetch_related("user", "project", "role")
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

    def save(self, *args, **kwargs):
        get_token_for_user(self, "cancel_account")
        super().save(*args, **kwargs)

    def cancel(self):
        self.username = slugify_uniquely("deleted-user", User, slugfield="username")
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
        self.delete_photo()
        self.save()
        self.auth_data.all().delete()

    def delete_photo(self):
        # Removing thumbnails
        thumbnailer = get_thumbnailer(self.photo)
        thumbnailer.delete_thumbnails()

        # Removing original photo
        if self.photo:
            storage, path = self.photo.storage, self.photo.path
            storage.delete(path)

        self.photo = None


class Role(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, null=False, blank=True,
                            verbose_name=_("slug"))
    permissions = TextArrayField(blank=True, null=True,
                                 default=[],
                                 verbose_name=_("permissions"),
                                 choices=MEMBERS_PERMISSIONS)
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    # null=True is for make work django 1.7 migrations. project
    # field causes some circular dependencies, and due to this
    # it can not be serialized in one transactional migration.
    project = models.ForeignKey("projects.Project", null=True, blank=False,
                                related_name="roles", verbose_name=_("project"))
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
        permissions = (
            ("view_role", "Can view role"),
        )

    def __str__(self):
        return self.name


class AuthData(models.Model):
    user = models.ForeignKey('users.User', related_name="auth_data")
    key = models.SlugField(max_length=50)
    value = models.CharField(max_length=300)
    extra = JsonField()

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
