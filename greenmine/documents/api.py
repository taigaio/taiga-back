from rest_framework import generics

from greenmine.documents.serializers import DocumentSerializer
from greenmine.documents.models import Document


class DocumentList(generics.ListCreateAPIView):
    model = Document
    serializer_class = DocumentSerializer


class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Document
    serializer_class = DocumentSerializer
