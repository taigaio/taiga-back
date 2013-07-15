# -*- coding: utf-8 -*-

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.http import Http404

from rest_framework import generics

from greenmine.wiki.serializers import WikiPageSerializer, WikiPageAttachmentSerializer
from greenmine.wiki.models import WikiPage, WikiPageAttachment
from greenmine.wiki.permissions import WikiPageDetailPermission, WikiPageAttachmentDetailPermission


class WikiPageList(generics.ListCreateAPIView):
    model = WikiPage
    serializer_class = WikiPageSerializer

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user


class WikiPageDetail(generics.RetrieveUpdateDestroyAPIView):
    model = WikiPage
    serializer_class = WikiPageSerializer
    permission_classes = (WikiPageDetailPermission,)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        queryset = queryset.filter(project=self.kwargs["projectid"],
                                   slug=self.kwargs["slug"])
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(_("No {verbose_name} found matching the query").format(
                          verbose_name=queryset.model._meta.verbose_name))
        return obj


class WikiPageAttachmentList(generics.ListCreateAPIView):
    model = WikiPageAttachment
    serializer_class = WikiPageAttachmentSerializer

    def get_queryset(self):
        return self.model.objects.filter(wikipage__project__members=self.request.user)


class WikiPageAttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = WikiPageAttachment
    serializer_class = WikiPageAttachmentSerializer
    permission_classes = (WikiPageAttachmentDetailPermission,)
