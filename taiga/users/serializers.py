# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from taiga.base.api import serializers
from taiga.base.fields import PgArrayField, TagsField

from taiga.projects.models import Project
from .models import User, Role
from .services import get_photo_or_gravatar_url, get_big_photo_or_gravatar_url

from collections import namedtuple

import re


######################################################
## User
######################################################

class ContactProjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "slug", "name")


class UserSerializer(serializers.ModelSerializer):
    full_name_display = serializers.SerializerMethodField("get_full_name_display")
    photo = serializers.SerializerMethodField("get_photo")
    big_photo = serializers.SerializerMethodField("get_big_photo")
    roles = serializers.SerializerMethodField("get_roles")
    projects_with_me = serializers.SerializerMethodField("get_projects_with_me")

    class Meta:
        model = User
        # IMPORTANT: Maintain the UserAdminSerializer Meta up to date
        # with this info (including there the email)
        fields = ("id", "username", "full_name", "full_name_display",
                  "color", "bio", "lang", "theme", "timezone", "is_active",
                  "photo", "big_photo", "roles", "projects_with_me")
        read_only_fields = ("id",)

    def validate_username(self, attrs, source):
        value = attrs[source]
        validator = validators.RegexValidator(re.compile('^[\w.-]+$'), _("invalid username"),
                                              _("invalid"))

        try:
            validator(value)
        except ValidationError:
            raise serializers.ValidationError(_("Required. 255 characters or fewer. Letters, "
                                                "numbers and /./-/_ characters'"))

        if (self.object and
                self.object.username != value and
                User.objects.filter(username=value).exists()):
            raise serializers.ValidationError(_("Invalid username. Try with a different one."))

        return attrs

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_photo_or_gravatar_url(user)

    def get_big_photo(self, user):
        return get_big_photo_or_gravatar_url(user)

    def get_roles(self, user):
        return user.memberships. order_by("role__name").values_list("role__name", flat=True).distinct()

    def get_projects_with_me(self, user):
        request = self.context.get("request", None)
        requesting_user = request and request.user or None

        if not requesting_user or not requesting_user.is_authenticated():
            return []

        else:
            project_ids = requesting_user.memberships.values_list("project__id", flat=True)
            memberships = user.memberships.filter(project__id__in=project_ids)
            project_ids = memberships.values_list("project__id", flat=True)
            projects = Project.objects.filter(id__in=project_ids)
            return ContactProjectDetailSerializer(projects, many=True).data

class UserAdminSerializer(UserSerializer):
    class Meta:
        model = User
        # IMPORTANT: Maintain the UserSerializer Meta up to date
        # with this info (including here the email)
        fields = ("id", "username", "full_name", "full_name_display", "email",
                  "color", "bio", "lang", "theme", "timezone", "is_active", "photo",
                  "big_photo")
        read_only_fields = ("id", "email")


class UserBasicInfoSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ("username", "full_name_display","photo", "big_photo", "is_active")


class RecoverySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(min_length=6)


class ChangeEmailSerializer(serializers.Serializer):
    email_token = serializers.CharField(max_length=200)


class CancelAccountSerializer(serializers.Serializer):
    cancel_token = serializers.CharField(max_length=200)


######################################################
## Role
######################################################

class RoleSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField("get_members_count")
    permissions = PgArrayField(required=False)

    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'computable', 'project', 'order', 'members_count')
        i18n_fields = ("name",)

    def get_members_count(self, obj):
        return obj.memberships.count()


class ProjectRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'slug', 'order', 'computable')
        i18n_fields = ("name",)


######################################################
## Like
######################################################


class HighLightedContentSerializer(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.IntegerField()
    ref = serializers.IntegerField()
    slug = serializers.CharField()
    name = serializers.CharField()
    subject = serializers.CharField()
    description = serializers.SerializerMethodField("get_description")
    assigned_to = serializers.IntegerField()
    status = serializers.CharField()
    status_color = serializers.CharField()
    tags_colors = serializers.SerializerMethodField("get_tags_color")
    created_date = serializers.DateTimeField()
    is_private = serializers.SerializerMethodField("get_is_private")

    project = serializers.SerializerMethodField("get_project")
    project_name = serializers.SerializerMethodField("get_project_name")
    project_slug = serializers.SerializerMethodField("get_project_slug")
    project_is_private = serializers.SerializerMethodField("get_project_is_private")

    assigned_to_username = serializers.CharField()
    assigned_to_full_name = serializers.CharField()
    assigned_to_photo = serializers.SerializerMethodField("get_photo")

    is_watcher = serializers.SerializerMethodField("get_is_watcher")
    total_watchers = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        # Don't pass the extra ids args up to the superclass
        self.user_watching = kwargs.pop("user_watching", {})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def _none_if_project(self, obj, property):
        type = obj.get("type", "")
        if type == "project":
            return None

        return obj.get(property)

    def _none_if_not_project(self, obj, property):
        type = obj.get("type", "")
        if type != "project":
            return None

        return obj.get(property)

    def get_project(self, obj):
        return self._none_if_project(obj, "project")

    def get_is_private(self, obj):
        return self._none_if_not_project(obj, "project_is_private")

    def get_project_name(self, obj):
        return self._none_if_project(obj, "project_name")

    def get_description(self, obj):
        return self._none_if_not_project(obj, "description")

    def get_project_slug(self, obj):
        return self._none_if_project(obj, "project_slug")

    def get_project_is_private(self, obj):
        return self._none_if_project(obj, "project_is_private")

    def get_photo(self, obj):
        type = obj.get("type", "")
        if type == "project":
            return None

        UserData = namedtuple("UserData", ["photo", "email"])
        user_data = UserData(photo=obj["assigned_to_photo"], email=obj.get("assigned_to_email") or "")
        return get_photo_or_gravatar_url(user_data)

    def get_tags_color(self, obj):
        tags = obj.get("tags", [])
        tags = tags if tags is not None else []
        tags_colors = obj.get("tags_colors", [])
        tags_colors = tags_colors if tags_colors is not None else []
        return [{"name": tc[0], "color": tc[1]} for tc in tags_colors if tc[0] in tags]

    def get_is_watcher(self, obj):
        return obj["id"] in self.user_watching.get(obj["type"], [])


class LikedObjectSerializer(HighLightedContentSerializer):
    is_fan = serializers.SerializerMethodField("get_is_fan")
    total_fans = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        # Don't pass the extra ids args up to the superclass
        self.user_likes  = kwargs.pop("user_likes", {})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def get_is_fan(self, obj):
        return obj["id"] in self.user_likes.get(obj["type"], [])


class VotedObjectSerializer(HighLightedContentSerializer):
    is_voter = serializers.SerializerMethodField("get_is_voter")
    total_voters = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        # Don't pass the extra ids args up to the superclass
        self.user_votes  = kwargs.pop("user_votes", {})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def get_is_voter(self, obj):
        return obj["id"] in self.user_votes.get(obj["type"], [])
