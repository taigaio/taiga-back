# -*- coding: utf-8 -*-

from rest_framework import serializers
from taiga.base.users.serializers import UserSerializer

from .models import Domain, DomainMember


class DomainSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField('get_projects')

    class Meta:
        model = Domain
        fields = ('public_register', 'default_language', "projects")

    def get_projects(self, obj):
        return map(lambda x: {"id": x.id, "name": x.name, "slug": x.slug}, obj.projects.all().order_by('name'))


class DomainMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = DomainMember
