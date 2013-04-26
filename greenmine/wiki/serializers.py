# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.wiki.models import WikiPage, WikiPageAttachment


class WikiPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPage
        fields = ()


class WikiPageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPageAttachment
        fields = ()
