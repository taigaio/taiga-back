# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField, I18NField

from taiga.base.utils.thumbnails import get_thumbnail_url

from taiga.projects.models import Project
from .services import get_user_photo_url, get_user_big_photo_url
from taiga.users.gravatar import get_user_gravatar_id
from taiga.users.models import User


######################################################
# User
######################################################

class ContactProjectDetailSerializer(serializers.LightSerializer):
    id = Field()
    slug = Field()
    name = Field()


class UserSerializer(serializers.LightSerializer):
    id = Field()
    username = Field()
    full_name = Field()
    full_name_display = MethodField()
    color = Field()
    bio = Field()
    lang = Field()
    theme = Field()
    timezone = Field()
    is_active = Field()
    photo = MethodField()
    big_photo = MethodField()
    gravatar_id = MethodField()
    roles = MethodField()

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_user_photo_url(user)

    def get_big_photo(self, user):
        return get_user_big_photo_url(user)

    def get_gravatar_id(self, user):
        return get_user_gravatar_id(user)

    def get_roles(self, user):
        if hasattr(user, "roles_attr"):
            return user.roles_attr

        return user.memberships.order_by("role__name").values_list("role__name", flat=True).distinct()


class UserAdminSerializer(UserSerializer):
    total_private_projects = MethodField()
    total_public_projects = MethodField()
    email = Field()
    uuid = Field()
    date_joined = Field()
    read_new_terms = Field()
    accepted_terms = Field()
    max_private_projects = Field()
    max_public_projects = Field()
    max_memberships_private_projects = Field()
    max_memberships_public_projects = Field()
    verified_email = Field()

    def get_total_private_projects(self, user):
        return user.owned_projects.filter(is_private=True).count()

    def get_total_public_projects(self, user):
        return user.owned_projects.filter(is_private=False).count()


class UserBasicInfoSerializer(serializers.LightSerializer):
    username = Field()
    full_name_display = MethodField()
    photo = MethodField()
    big_photo = MethodField()
    gravatar_id = MethodField()
    is_active = Field()
    id = Field()

    def get_full_name_display(self, obj):
        return obj.get_full_name()

    def get_photo(self, obj):
        return get_user_photo_url(obj)

    def get_big_photo(self, obj):
        return get_user_big_photo_url(obj)

    def get_gravatar_id(self, obj):
        return get_user_gravatar_id(obj)

    def to_value(self, instance):
        if instance is None:
            return None

        return super().to_value(instance)


######################################################
# Role
######################################################

class RoleSerializer(serializers.LightSerializer):
    id = Field()
    name = Field()
    slug = Field()
    project = Field(attr="project_id")
    order = Field()
    computable = Field()
    permissions = Field()
    members_count = MethodField()

    def get_members_count(self, obj):
        return obj.memberships.count()


######################################################
# Like
######################################################

class HighLightedContentSerializer(serializers.LightSerializer):
    type = Field()
    id = Field()
    ref = Field()
    slug = Field()
    name = Field()
    subject = Field()
    description = MethodField()
    assigned_to = Field()
    status = Field()
    status_color = Field()
    tags_colors = MethodField()
    created_date = Field()
    is_private = MethodField()
    logo_small_url = MethodField()

    project = MethodField()
    project_name = MethodField()
    project_slug = MethodField()
    project_is_private = MethodField()
    project_blocked_code = Field()

    assigned_to = Field(attr="assigned_to_id")
    assigned_to_extra_info = MethodField()

    is_watcher = MethodField()
    total_watchers = Field()

    def __init__(self, *args, **kwargs):
        # Don't pass the extra ids args up to the superclass
        self.user_watching = kwargs.pop("user_watching", {})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def _none_if_project(self, obj, property):
        type = getattr(obj, "type", "")
        if type == "project":
            return None

        return getattr(obj, property)

    def _none_if_not_project(self, obj, property):
        type = getattr(obj, "type", "")
        if type != "project":
            return None

        return getattr(obj, property)

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

    def get_logo_small_url(self, obj):
        logo = self._none_if_not_project(obj, "logo")
        if logo:
            return get_thumbnail_url(logo, settings.THN_LOGO_SMALL)
        return None

    def get_assigned_to_extra_info(self, obj):
        assigned_to = None
        if obj.assigned_to_extra_info is not None:
            assigned_to = User(**obj.assigned_to_extra_info)
        return UserBasicInfoSerializer(assigned_to).data

    def get_tags_colors(self, obj):
        tags = getattr(obj, "tags", [])
        tags = tags if tags is not None else []
        tags_colors = getattr(obj, "tags_colors", [])
        tags_colors = tags_colors if tags_colors is not None else []
        return [{"name": tc[0], "color": tc[1]} for tc in tags_colors if tc[0] in tags]

    def get_is_watcher(self, obj):
        return obj.id in self.user_watching.get(obj.type, [])


class LikedObjectSerializer(HighLightedContentSerializer):
    is_fan = MethodField()
    total_fans = Field()

    def __init__(self, *args, **kwargs):
        # Don't pass the extra ids args up to the superclass
        self.user_likes = kwargs.pop("user_likes", {})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def get_is_fan(self, obj):
        return obj.id in self.user_likes.get(obj.type, [])


class VotedObjectSerializer(HighLightedContentSerializer):
    is_voter = MethodField()
    total_voters = Field()

    def __init__(self, *args, **kwargs):
        # Don't pass the extra ids args up to the superclass
        self.user_votes = kwargs.pop("user_votes", {})

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def get_is_voter(self, obj):
        return obj.id in self.user_votes.get(obj.type, [])
