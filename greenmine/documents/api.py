# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

from greenmine.documents.models import *

class DocumentResource(ModelResource):
    class Meta:
        queryset = Document.objects.all()
        resource_name = 'document'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
