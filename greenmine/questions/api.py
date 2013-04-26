# -*- coding: utf-8 -*-

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from greenmine.questions.serializers import QuestionSerializer
from greenmine.questions.models import Question
from greenmine.questions.permissions import QuestionDetailPermission

import reversion

class QuestionList(generics.ListCreateAPIView):
    model = Question
    serializer_class = QuestionSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user


class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Question
    serializer_class = QuestionSerializer
    permission_classes = (IsAuthenticated, QuestionDetailPermission,)

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])
