from rest_framework import serializers

class UserLogged(object):
    def __init__(self, token, username, first_name, last_name, email, last_login):
        self.token = token
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.last_login = last_login


class LoginSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=40)
    username = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    last_login = serializers.DateTimeField()

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            instance.token = attrs.get('token', None)
            instance.username = attrs.get('username', instance.username)
            instance.first_name = attrs.get('first_name', instance.first_name)
            instance.last_name = attrs.get('last_name', instance.last_name)
            instance.email = attrs.get('email', instance.email)
            instance.last_login = attrs.get('last_login', instance.last_login)
            return instance
        return UserLogged(**attrs)
