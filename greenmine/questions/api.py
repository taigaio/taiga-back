# -*- coding: utf-8 -*-

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from . import serializers
from . import models
from . import permissions

import reversion


class QuestionList(generics.ListCreateAPIView):
    model = models.Question
    serializer_class = serializers.QuestionSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return super(QuestionList, self).filter(project__members=self.request.user)


    def pre_save(self, obj):
        obj.owner = self.request.user


class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = models.Question
    serializer_class = serializers.QuestionSerializer
    permission_classes = (IsAuthenticated, permissions.QuestionDetailPermission,)

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])
