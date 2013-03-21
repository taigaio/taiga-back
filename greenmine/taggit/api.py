# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

from greenmine.taggit.models import Tag, TaggedItem


class TagResource(ModelResource):
    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class TaggedItemResource(ModelResource):
    class Meta:
        queryset = TaggedItem.objects.all()
        resource_name = 'taggeditem'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
