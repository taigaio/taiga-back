# -*- coding: utf-8 -*-

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.http import Http404

from rest_framework import generics
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated

from greenmine.base import api as api_views
from greenmine.base import filters

from . import models
from . import serializers
from . import permissions


class WikiViewSet(api_views.ModelCrudViewSet):
    model = models.WikiPage
    serializer_class = serializers.WikiPageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "slug"]

    def get_queryset(self):
        qs = super(WikiViewSet, self).get_queryset()
        return qs.filter(project__members=self.request.user)

    def pre_save(self, obj):
        if not obj.owner:
            obj.owner = self.request.user
