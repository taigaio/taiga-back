from rest_framework import serializers


class ResolverSerializer(serializers.Serializer):
    project = serializers.CharField(max_length=512, required=True)
    milestone = serializers.CharField(max_length=512, required=False)
    us = serializers.IntegerField(required=False)
    task = serializers.IntegerField(required=False)
    issue = serializers.IntegerField(required=False)
