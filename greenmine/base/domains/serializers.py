# -*- coding: utf-8 -*-

from rest_framework import serializers
from .models import Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('public_register', 'default_language')
