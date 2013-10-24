# -*- coding: utf-8 -*-

from rest_framework import serializers
from .models import User, Role


class UserSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField('get_projects')
    full_name = serializers.CharField(source='get_full_name', required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'email',
                  'color', 'description', 'default_language', 'default_timezone',
                  'is_active', 'photo', 'projects', 'notify_level',
                  'notify_changes_by_me')

    def get_projects(self, obj):
        return [{"id": x.id, "name": x.name} for x in obj.projects.all()]


class RecoverySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=6)

    def validate_token(self, attrs, source):
        token = attrs[source]
        try:
            user = User.objects.get(token=token)
        except User.DoesNotExist:
            raise serializers.ValidationError("invalid token")

        return attrs


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'slug', 'permissions', 'computable')
