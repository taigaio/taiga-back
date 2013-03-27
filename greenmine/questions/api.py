
from rest_framework import generics

from greenmine.questions.serializers import QuestionSerializer, QuestionResponseSerializer
from greenmine.questions.models import Question, QuestionResponse


class QuestionList(generics.ListCreateAPIView):
    model = Question
    serializer_class = QuestionSerializer


class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Question
    serializer_class = QuestionSerializer


class QuestionResponseList(generics.ListCreateAPIView):
    model = QuestionResponse
    serializer_class = QuestionResponseSerializer


class QuestionResponseDetail(generics.RetrieveUpdateDestroyAPIView):
    model = QuestionResponse
    serializer_class = QuestionResponseSerializer
