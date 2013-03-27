from rest_framework import serializers

from greenmine.documents.models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ()
