# -*- coding: utf-8 -*-

from rest_framework import serializers

from . import models


class WikiPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WikiPage


class WikiPageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WikiPageAttachment
