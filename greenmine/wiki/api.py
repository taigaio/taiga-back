# myapp/api.py
from tastypie.resources import ModelResource
from greenmine.wiki.models import *

class WikiPageResource(ModelResource):
    class Meta:
        queryset = WikiPage.objects.all()
        resource_name = 'wikipage'


class WikiPageHistoryResource(ModelResource):
    class Meta:
        queryset = WikiPageHistory.objects.all()
        resource_name = 'wikipagehistory'


class WikiPageAttachmentResource(ModelResource):
    class Meta:
        queryset = WikiPageAttachment.objects.all()
        resource_name = 'wikipageattachment'
