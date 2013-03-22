# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group

from greenmine.scrum.models import Project

class Profile(models.Model):
    user = models.OneToOneField("auth.User", related_name='profile')
    description = models.TextField(blank=True)
    photo = models.FileField(upload_to="files/msg", max_length=500, null=True,
                             blank=True)

    default_language = models.CharField(max_length=20, null=True, blank=True,
                                        default=None)
    default_timezone = models.CharField(max_length=20, null=True, blank=True,
                                        default=None)
    token = models.CharField(max_length=200, unique=True, null=True,
                             blank=True, default=None)
    colorize_tags = models.BooleanField(default=False)


class Role(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    permissions = models.ManyToManyField('auth.Permission',
        verbose_name=_('permissions'), blank=True)

    def __unicode__(self):
        return unicode(self.name)

if not hasattr(Group, 'role'):
    field = models.ForeignKey(Role, blank=False, null=False, related_name='groups')
    field.contribute_to_class(Group, 'role')

if not hasattr(Group, 'project'):
    field = models.ForeignKey(Project, blank=False, null=False, related_name='groups')
    field.contribute_to_class(Group, 'project')


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Create void user profile if instance is a new user.
    """
    if created and not Profile.objects.filter(user=instance).exists():
        Profile.objects.create(user=instance)

@receiver(post_save, sender=Role)
def role_post_save(sender, instance, **kwargs):
    """
    Recalculate projects groups
    """
    from greenmine.profile.services import RoleGroupsService
    RoleGroupsService().replicate_role_on_all_projects(instance)

@receiver(m2m_changed, sender=Role.permissions.through)
def role_m2m_changed(sender, instance, **kwargs):
    """
    Recalculate projects groups
    """
    from greenmine.profile.services import RoleGroupsService
    RoleGroupsService().replicate_role_on_all_projects(instance)
