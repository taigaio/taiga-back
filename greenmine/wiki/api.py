# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

from greenmine.wiki.models import WikiPage, WikiPageHistory, WikiPageAttachment


class WikiPageResource(ModelResource):
    class Meta:
        queryset = WikiPage.objects.all()
        resource_name = 'wikipage'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class WikiPageHistoryResource(ModelResource):
    class Meta:
        queryset = WikiPageHistory.objects.all()
        resource_name = 'wikipagehistory'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class WikiPageAttachmentResource(ModelResource):
    class Meta:
        queryset = WikiPageAttachment.objects.all()
        resource_name = 'wikipageattachment'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
