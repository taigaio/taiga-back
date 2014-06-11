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

from os import path
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from taiga.base.serializers import PickleField, JsonField
from taiga.users.models import Role, User

from . import models


# User Stories common serializers

class PointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Points


class UserStoryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserStoryStatus


# Task common serializers

class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskStatus


# Issues common serializers

class SeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Severity


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Priority


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueStatus


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueType


# Projects

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Membership
        read_only_fields = ("user",)


class ProjectMembershipSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', required=False)
    full_name = serializers.CharField(source='user.get_full_name', required=False)
    color = serializers.CharField(source='user.color', required=False)

    class Meta:
        model = models.Membership


class ProjectSerializer(serializers.ModelSerializer):
    tags = PickleField(required=False)
    stars = serializers.SerializerMethodField("get_stars_number")

    class Meta:
        model = models.Project
        read_only_fields = ("created_date", "modified_date", "owner")
        exclude = ("last_us_ref", "last_task_ref", "last_issue_ref")

    def get_stars_number(self, obj):
        # The "stars_count" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "stars_count", 0)


class ProjectDetailSerializer(ProjectSerializer):
    roles = serializers.SerializerMethodField("get_list_of_roles")
    memberships = serializers.SerializerMethodField("get_membership")
    active_memberships = serializers.SerializerMethodField("get_active_membership")
    us_statuses = UserStoryStatusSerializer(many=True, required=False)       # User Stories
    points = PointsSerializer(many=True, required=False)
    task_statuses = TaskStatusSerializer(many=True, required=False)          # Tasks
    priorities = PrioritySerializer(many=True, required=False)               # Issues
    severities = SeveritySerializer(many=True, required=False)
    issue_statuses = IssueStatusSerializer(many=True, required=False)
    issue_types = IssueTypeSerializer(many=True, required=False)

    def get_membership(self, obj):
        qs = obj.memberships.order_by('user__full_name', 'user__username')
        qs = qs.select_related("role", "user")

        serializer = ProjectMembershipSerializer(qs, many=True)
        return serializer.data

    def get_active_membership(self, obj):
        qs = obj.memberships.filter(user__isnull=False)
        qs = qs.order_by('user__full_name', 'user__username')
        qs = qs.select_related("role", "user")

        serializer = ProjectMembershipSerializer(qs, many=True)
        return serializer.data

    def get_list_of_roles(self, obj):
        roles_list = []

        if obj and obj.memberships:
            roles_list = [{
                "id": role["role__id"],
                "name": role["role__name"],
                "slug": role["role__slug"],
                "order": role["role__order"],
                "computable": role["role__computable"],
            } for role in obj.memberships.values("role__id", "role__name", "role__slug", "role__order",
                                                 "role__computable")
                                         .order_by("role__order", "role__id")
                                         .distinct("role__order", "role__id")]

        return roles_list


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'computable', 'project', 'order')


class ProjectTemplateSerializer(serializers.ModelSerializer):
    default_options = JsonField(required=False, label=_("Default options"))
    us_statuses = JsonField(required=False, label=_("User story's statuses"))
    points = JsonField(required=False, label=_("Points"))
    task_statuses = JsonField(required=False, label=_("Task's statuses"))
    issue_statuses = JsonField(required=False, label=_("Issue's statuses"))
    issue_types = JsonField(required=False, label=_("Issue's types"))
    priorities = JsonField(required=False, label=_("Priorities"))
    severities = JsonField(required=False, label=_("Severities"))
    roles = JsonField(required=False, label=_("Roles"))

    class Meta:
        model = models.ProjectTemplate


class StarredSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = ['id', 'name', 'slug']
