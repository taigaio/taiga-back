from rest_framework import serializers

from greenmine.questions.models import Question, QuestionResponse


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ()


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResponse
        fields = ()
