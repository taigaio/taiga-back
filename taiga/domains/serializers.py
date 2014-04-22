# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

from django.conf import settings

from rest_framework import serializers
from taiga.users.serializers import UserSerializer

from .models import Domain, DomainMember


class DomainSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField('get_projects')
    default_project_template = serializers.SerializerMethodField('get_default_project_template')

    class Meta:
        model = Domain
        fields = ('public_register', 'default_language', "projects", "default_project_template")

    def get_projects(self, obj):
        return map(lambda x: {"id": x.id, "name": x.name, "slug": x.slug, "owner": x.owner.id}, obj.projects.all().order_by('name'))

    def get_default_project_template(self, obj):
        return settings.DEFAULT_PROJECT_TEMPLATE


class DomainMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = DomainMember
