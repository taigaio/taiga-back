# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Profile


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Create void user profile if instance is a new user.
    """
    if created and not Profile.objects.filter(user=instance).exists():
        Profile.objects.create(user=instance)
