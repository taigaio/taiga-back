# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from greenmine.core.fields import DictField, ListField
from greenmine.core.utils import iter_points

import datetime
import re


class Profile(models.Model):
    user = models.OneToOneField("auth.User", related_name='profile')
    description = models.TextField(blank=True)
    photo = models.FileField(upload_to="files/msg",
        max_length=500, null=True, blank=True)

    default_language = models.CharField(max_length=20,
        null=True, blank=True, default=None)
    default_timezone = models.CharField(max_length=20,
        null=True, blank=True, default=None)
    token = models.CharField(max_length=200, unique=True,
        null=True, blank=True, default=None)
    colorize_tags = models.BooleanField(default=False)


class Role(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)

    project_view = models.BooleanField(default=True)
    project_edit = models.BooleanField(default=False)
    project_delete = models.BooleanField(default=False)
    userstory_view = models.BooleanField(default=True)
    userstory_create = models.BooleanField(default=False)
    userstory_edit = models.BooleanField(default=False)
    userstory_delete = models.BooleanField(default=False)
    milestone_view = models.BooleanField(default=True)
    milestone_create = models.BooleanField(default=False)
    milestone_edit = models.BooleanField(default=False)
    milestone_delete = models.BooleanField(default=False)
    task_view = models.BooleanField(default=True)
    task_create = models.BooleanField(default=False)
    task_edit = models.BooleanField(default=False)
    task_delete = models.BooleanField(default=False)
    wiki_view = models.BooleanField(default=True)
    wiki_create = models.BooleanField(default=False)
    wiki_edit = models.BooleanField(default=False)
    wiki_delete = models.BooleanField(default=False)
    question_view = models.BooleanField(default=True)
    question_create = models.BooleanField(default=True)
    question_edit = models.BooleanField(default=True)
    question_delete = models.BooleanField(default=False)
    document_view = models.BooleanField(default=True)
    document_create = models.BooleanField(default=True)
    document_edit = models.BooleanField(default=True)
    document_delete = models.BooleanField(default=True)


from . import sigdispatch
