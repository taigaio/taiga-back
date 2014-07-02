# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from .models import User
from .services import get_photo_or_gravatar_url


class UserSerializer(serializers.ModelSerializer):
    full_name_display = serializers.SerializerMethodField("get_full_name_display")
    photo = serializers.SerializerMethodField("get_photo")

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name', 'full_name_display', 'email', 'github_id',
                  'color', 'bio', 'default_language', 'default_timezone',
                  'is_active', 'photo')

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_photo_or_gravatar_url(user)


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
