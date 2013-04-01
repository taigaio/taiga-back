from rest_framework import generics

from greenmine.wiki.serializers import WikiPageSerializer, WikiPageAttachmentSerializer
from greenmine.wiki.models import WikiPage, WikiPageAttachment
from greenmine.wiki.permissions import WikiPageDetailPermission, WikiPageAttachmentDetailPermission


class WikiPageList(generics.ListCreateAPIView):
    model = WikiPage
    serializer_class = WikiPageSerializer

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user


class WikiPageDetail(generics.RetrieveUpdateDestroyAPIView):
    model = WikiPage
    serializer_class = WikiPageSerializer
    permission_classes = (WikiPageDetailPermission,)


class WikiPageAttachmentList(generics.ListCreateAPIView):
    model = WikiPageAttachment
    serializer_class = WikiPageAttachmentSerializer

    def get_queryset(self):
        return self.model.objects.filter(wikipage__project__members=self.request.user)


class WikiPageAttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = WikiPageAttachment
    serializer_class = WikiPageAttachmentSerializer
    permission_classes = (WikiPageAttachmentDetailPermission,)
