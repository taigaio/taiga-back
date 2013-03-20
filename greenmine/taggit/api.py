# myapp/api.py
from tastypie.resources import ModelResource
from greenmine.taggit.models import *

class TagResource(ModelResource):
    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'

class TaggedItemResource(ModelResource):
    class Meta:
        queryset = TaggedItem.objects.all()
        resource_name = 'taggeditem'
