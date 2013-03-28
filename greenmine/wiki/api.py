from rest_framework import generics

from greenmine.wiki.serializers import WikiPageSerializer, WikiPageAttachmentSerializer
from greenmine.wiki.models import WikiPage, WikiPageAttachment


class WikiPageList(generics.ListCreateAPIView):
    model = WikiPage
    serializer_class = WikiPageSerializer


class WikiPageDetail(generics.RetrieveUpdateDestroyAPIView):
    model = WikiPage
    serializer_class = WikiPageSerializer


class WikiPageAttachmentList(generics.ListCreateAPIView):
    model = WikiPageAttachment
    serializer_class = WikiPageAttachmentSerializer


class WikiPageAttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = WikiPageAttachment
    serializer_class = WikiPageAttachmentSerializer
