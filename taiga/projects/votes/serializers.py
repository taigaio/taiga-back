from rest_framework import serializers

from taiga.users.models import User


class VoterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name')
