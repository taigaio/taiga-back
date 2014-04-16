# -*- coding: utf-8 -*-

from rest_framework import serializers

class BaseRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(max_length=200)
    username = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=4)


class PublicRegisterSerializer(BaseRegisterSerializer):
    pass


class PrivateRegisterForNewUserSerializer(BaseRegisterSerializer):
    token = serializers.CharField(max_length=255, required=True)

class PrivateRegisterForExistingUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=4)
    token = serializers.CharField(max_length=255, required=True)
