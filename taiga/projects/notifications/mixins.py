# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from functools import partial
from operator import is_not

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from taiga.base import response
from taiga.base.decorators import detail_route
from taiga.base.api import serializers
from taiga.base.api.utils import get_object_or_404
from taiga.base.fields import WatchersField
from taiga.projects.notifications import services
from taiga.projects.notifications.utils import (attach_watchers_to_queryset,
    attach_is_watcher_to_queryset,
    attach_total_watchers_to_queryset)

from . serializers import WatcherSerializer



class WatchedResourceMixin:
    """
    Rest Framework resource mixin for resources susceptible
    to be notifiable about their changes.

    NOTE:
    - this mixin has hard dependency on HistoryMixin
    defined on history app and should be located always
    after it on inheritance definition.

    - the classes using this mixing must have a method:
    def pre_conditions_on_save(self, obj)
    """

    _not_notify = False

    def attach_watchers_attrs_to_queryset(self, queryset):
        queryset = attach_watchers_to_queryset(queryset)
        queryset = attach_total_watchers_to_queryset(queryset)
        if self.request.user.is_authenticated():
            queryset = attach_is_watcher_to_queryset(queryset, self.request.user)

        return queryset

    @detail_route(methods=["POST"])
    def watch(self, request, pk=None):
        obj = self.get_object()
        self.check_permissions(request, "watch", obj)
        self.pre_conditions_on_save(obj)
        services.add_watcher(obj, request.user)
        return response.Ok()

    @detail_route(methods=["POST"])
    def unwatch(self, request, pk=None):
        obj = self.get_object()
        self.check_permissions(request, "unwatch", obj)
        self.pre_conditions_on_save(obj)
        services.remove_watcher(obj, request.user)
        return response.Ok()

    def send_notifications(self, obj, history=None):
        """
        Shortcut method for resources with special save
        cases on actions methods that not uses standard
        `post_save` hook of drf resources.
        """
        if history is None:
            history = self.get_last_history()

        # If not history found, or it is empty. Do notthing.
        if not history:
            return

        if self._not_notify:
            return

        obj = self.get_object_for_snapshot(obj)

        # Process that analizes the corresponding diff and
        # some text fields for extract mentions and add them
        # to watchers before obtain a complete list of
        # notifiable users.
        services.analize_object_for_watchers(obj, history.comment, history.owner)

        # Get a complete list of notifiable users for current
        # object and send the change notification to them.
        services.send_notifications(obj, history=history)

    def post_save(self, obj, created=False):
        self.send_notifications(obj)
        super().post_save(obj, created)

    def pre_delete(self, obj):
        self.send_notifications(obj)
        super().pre_delete(obj)


class WatchedModelMixin(object):
    """
    Generic model mixin that makes model compatible
    with notification system.

    NOTE: is mandatory extend your model class with
    this mixin if you want send notifications about
    your model class.
    """

    def get_project(self) -> object:
        """
        Default implementation method for obtain a project
        instance from current object.

        It comes with generic default implementation
        that should works in almost all cases.
        """
        return self.project

    def get_watchers(self) -> object:
        """
        Default implementation method for obtain a list of
        watchers for current instance.
        """
        return services.get_watchers(self)

    def get_related_people(self) -> object:
        """
        Default implementation for obtain the related people of
        current instance.
        """
        return services.get_related_people(self)

    def get_watched(self, user_or_id):
        return services.get_watched(user_or_id, type(self))

    def add_watcher(self, user):
        services.add_watcher(self, user)

    def remove_watcher(self, user):
        services.remove_watcher(self, user)

    def get_owner(self) -> object:
        """
        Default implementation for obtain the owner of
        current instance.
        """
        return self.owner

    def get_assigned_to(self) -> object:
        """
        Default implementation for obtain the assigned
        user.
        """
        if hasattr(self, "assigned_to"):
            return self.assigned_to
        return None

    def get_participants(self) -> frozenset:
        """
        Default implementation for obtain the list
        of participans. It is mainly the owner and
        assigned user.
        """
        participants = (self.get_assigned_to(),
                        self.get_owner(),)
        is_not_none = partial(is_not, None)
        return frozenset(filter(is_not_none, participants))


class WatchedResourceModelSerializer(serializers.ModelSerializer):
    is_watcher = serializers.SerializerMethodField("get_is_watcher")
    total_watchers = serializers.SerializerMethodField("get_total_watchers")

    def get_is_watcher(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return user.is_authenticated() and user.is_watcher(obj)

        return False

    def get_total_watchers(self, obj):
        # The "total_watchers" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "total_watchers", 0) or 0


class EditableWatchedResourceModelSerializer(WatchedResourceModelSerializer):
    watchers = WatchersField(required=False)

    def restore_object(self, attrs, instance=None):
        #watchers is not a field from the model but can be attached in the get_queryset of the viewset.
        #If that's the case we need to remove it before calling the super method
        watcher_field = self.fields.pop("watchers", None)
        self.validate_watchers(attrs, "watchers")
        new_watcher_ids = attrs.pop("watchers", None)
        obj = super(WatchedResourceModelSerializer, self).restore_object(attrs, instance)

        #A partial update can exclude the watchers field or if the new instance can still not be saved
        if instance is None or new_watcher_ids is None:
            return obj

        new_watcher_ids = set(new_watcher_ids)
        old_watcher_ids = set(obj.get_watchers().values_list("id", flat=True))
        adding_watcher_ids = list(new_watcher_ids.difference(old_watcher_ids))
        removing_watcher_ids = list(old_watcher_ids.difference(new_watcher_ids))

        User = get_user_model()
        adding_users = get_user_model().objects.filter(id__in=adding_watcher_ids)
        removing_users = get_user_model().objects.filter(id__in=removing_watcher_ids)
        for user in adding_users:
            services.add_watcher(obj, user)

        for user in removing_users:
            services.remove_watcher(obj, user)

        obj.watchers = obj.get_watchers()

        return obj

    def to_native(self, obj):
        #if watchers wasn't attached via the get_queryset of the viewset we need to manually add it
        if obj is not None:
            if not hasattr(obj, "watchers"):
                obj.watchers = [user.id for user in obj.get_watchers()]

            request = self.context.get("request", None)
            user = request.user if request else None
            if user and user.is_authenticated():
                obj.is_watcher = user.id in obj.watchers

        return super(WatchedResourceModelSerializer, self).to_native(obj)

    def save(self, **kwargs):
        obj = super(EditableWatchedResourceModelSerializer, self).save(**kwargs)
        self.fields["watchers"] = WatchersField(required=False)
        obj.watchers = [user.id for user in obj.get_watchers()]
        return obj


class WatchersViewSetMixin:
    # Is a ModelListViewSet with two required params: permission_classes and resource_model
    serializer_class = WatcherSerializer
    list_serializer_class = WatcherSerializer
    permission_classes = None
    resource_model = None

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)

        self.check_permissions(request, 'retrieve', resource)

        try:
            self.object = resource.get_watchers().get(pk=pk)
        except ObjectDoesNotExist:  # or User.DoesNotExist
            return response.NotFound()

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    def list(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)

        self.check_permissions(request, 'list', resource)

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        resource = self.resource_model.objects.get(pk=self.kwargs.get("resource_id"))
        return resource.get_watchers()
