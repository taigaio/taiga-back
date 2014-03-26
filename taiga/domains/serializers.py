# Copyright 2014 Andrey Antukh <niwi@niwi.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# y ou may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rest_framework import serializers
from taiga.base.users.serializers import UserSerializer

from .models import Domain, DomainMember


class DomainSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField('get_projects')

    class Meta:
        model = Domain
        fields = ('public_register', 'default_language', "projects")

    def get_projects(self, obj):
        return map(lambda x: {"id": x.id, "name": x.name, "slug": x.slug, "owner": x.owner.id}, obj.projects.all().order_by('name'))


class DomainMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = DomainMember
