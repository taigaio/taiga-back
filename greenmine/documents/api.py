from rest_framework import generics

from greenmine.documents.serializers import DocumentSerializer
from greenmine.documents.models import Document
from greenmine.documents.permissions import DocumentDetailPermission


class DocumentList(generics.ListCreateAPIView):
    model = Document
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return self.model.objects.filter(project__members=self.request.user)


class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Document
    serializer_class = DocumentSerializer
    permission_classes = (DocumentDetailPermission,)
