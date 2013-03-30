
from rest_framework import generics

from greenmine.questions.serializers import QuestionSerializer, QuestionResponseSerializer
from greenmine.questions.models import Question, QuestionResponse
from greenmine.questions.permissions import QuestionDetailPermission, QuestionResponseDetailPermission


class QuestionList(generics.ListCreateAPIView):
    model = Question
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Question
    serializer_class = QuestionSerializer
    permission_classes = (QuestionDetailPermission,)


class QuestionResponseList(generics.ListCreateAPIView):
    model = QuestionResponse
    serializer_class = QuestionResponseSerializer

    def get_queryset(self):
        return self.model.objects.filter(question__project__members=self.request.user)

class QuestionResponseDetail(generics.RetrieveUpdateDestroyAPIView):
    model = QuestionResponse
    serializer_class = QuestionResponseSerializer
    permission_classes = (QuestionResponseDetailPermission,)
