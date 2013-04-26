# -*- coding: utf-8 -*-

from rest_framework import serializers

from . import models


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = ()
