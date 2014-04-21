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

from rest_framework import serializers

from taiga.base.serializers import PickleField
from taiga.base.users.models import Role

from . import models

from os import path


class AttachmentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField("get_name")
    url = serializers.SerializerMethodField("get_url")
    size = serializers.SerializerMethodField("get_size")

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "name", "attached_file", "size",
                  "created_date", "modified_date", "object_id", "url")
        read_only_fields = ("owner",)

    def get_name(self, obj):
        if obj.attached_file:
            return path.basename(obj.attached_file.path)
        return ""

    def get_url(self, obj):
        return obj.attached_file.url if obj and obj.attached_file else ""

    def get_size(self, obj):
        if obj.attached_file:
            try:
                return obj.attached_file.size
            except FileNotFoundError:
                pass
        return 0


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


# Questions common serializers

class QuestionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.QuestionStatus


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

    class Meta:
        model = models.Project
        read_only_fields = ("created_date", "modified_date", "owner", "domain")
        exclude = ("last_us_ref", "last_task_ref", "last_issue_ref")


class ProjectDetailSerializer(ProjectSerializer):
    list_of_milestones = serializers.SerializerMethodField("get_list_of_milestones")
    roles = serializers.SerializerMethodField("get_list_of_roles")
    memberships = ProjectMembershipSerializer(many=True, required=False)
    active_memberships = serializers.SerializerMethodField("get_active_membership")
    us_statuses = UserStoryStatusSerializer(many=True, required=False)       # User Stories
    points = PointsSerializer(many=True, required=False)
    task_statuses = TaskStatusSerializer(many=True, required=False)          # Tasks
    priorities = PrioritySerializer(many=True, required=False)               # Issues
    severities = SeveritySerializer(many=True, required=False)
    issue_statuses = IssueStatusSerializer(many=True, required=False)
    issue_types = IssueTypeSerializer(many=True, required=False)
    #question_statuses = QuestionStatusSerializer(many=True, required=False) # Questions

    def get_active_membership(self, obj):
        serializer = ProjectMembershipSerializer(obj.memberships.filter(user__isnull=False).order_by('user__first_name', 'user__last_name', 'user__username'), many=True)
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

    def get_list_of_milestones(self, obj):
        milestones_list = []

        if obj and obj.milestones:
            milestones_list = [{
                "id": milestone.id,
                "name": milestone.name,
                "finish_date": milestone.estimated_finish,
                "total_points": milestone.total_points,
                "closed_points": milestone.closed_points,
                "client_increment_points": milestone.client_increment_points,
                "team_increment_points": milestone.team_increment_points,
                "closed": milestone.closed
            } for milestone in obj.milestones.all().order_by("estimated_start")]

        return milestones_list


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'computable', 'project', 'order')
