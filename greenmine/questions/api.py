# myapp/api.py
from tastypie.resources import ModelResource
from greenmine.questions.models import *

class QuestionResource(ModelResource):
    class Meta:
        queryset = Question.objects.all()
        resource_name = 'question'

class QuestionResponseResource(ModelResource):
    class Meta:
        queryset = QuestionResponse.objects.all()
        resource_name = 'questionresponse'
