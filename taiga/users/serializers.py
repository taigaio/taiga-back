# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission

from rest_framework import serializers
from .models import User, Role


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'email',
                  'color', 'description', 'default_language', 'default_timezone',
                  'is_active', 'photo', 'notify_level', 'notify_changes_by_me')


class RecoverySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=6)

    def validate_token(self, attrs, source):
        token = attrs[source]
        try:
            user = User.objects.get(token=token)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("invalid token"))

        return attrs
