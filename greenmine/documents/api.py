# myapp/api.py
from tastypie.resources import ModelResource
from greenmine.documents.models import *

class DocumentResource(ModelResource):
    class Meta:
        queryset = Document.objects.all()
        resource_name = 'document'
