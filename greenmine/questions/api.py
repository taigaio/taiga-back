# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

from greenmine.questions.models import Question, QuestionResponse


class QuestionResource(ModelResource):
    class Meta:
        queryset = Question.objects.all()
        resource_name = 'question'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class QuestionResponseResource(ModelResource):
    class Meta:
        queryset = QuestionResponse.objects.all()
        resource_name = 'questionresponse'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
