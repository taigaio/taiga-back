# -*- coding: utf-8 -*-

from rest_framework import serializers


class SearchSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    model_name = serializers.CharField(max_length=255)
    pk = serializers.IntegerField()
    score = serializers.FloatField()
    stored_fields = serializers.SerializerMethodField('get_stored_fields')

    def get_stored_fields(self, obj):
        return obj.get_stored_fields()

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            return instance
        return attrs
