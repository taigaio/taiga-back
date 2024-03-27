# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from functools import partial
from operator import is_not

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from taiga.base import response
from taiga.base.decorators import detail_route
from taiga.base.api import serializers
from taiga.base.api.utils import get_object_or_error
from taiga.base.fields import WatchersField, MethodField
from taiga.projects.notifications import services

from . apps import signal_assigned_to
from . apps import signal_assigned_users
from . apps import signal_comment
from . apps import signal_comment_mentions
from . apps import signal_mentions
from . apps import signal_watchers_added
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
    _old_watchers = None
    _old_mentions = []

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
        services.analize_object_for_watchers(obj, history.comment,
                                             history.owner)

        # Get a complete list of notifiable users for current
        # object and send the change notification to them.
        services.send_notifications(obj, history=history)

    def update(self, request, *args, **kwargs):
        if not getattr(self, 'object', None):
            self.object = self.get_object_or_none()

        obj = self.object
        if obj and obj.id:
            if hasattr(obj, "watchers"):
                self._old_watchers = [
                    watcher.id for watcher in obj.get_watchers()
                ]

            mention_fields = ['description', 'content']
            for field_name in mention_fields:
                if not hasattr(obj, field_name) or not hasattr(obj, "get_project"):
                    continue
                self._old_mentions += services.get_mentions(obj.get_project(), getattr(obj, field_name))

        return super().update(request, *args, **kwargs)

    def post_save(self, obj, created=False):
        self.create_web_notifications_for_added_watchers(obj)
        self.create_web_notifications_for_mentioned_users(obj)

        mentions = self.create_web_notifications_for_mentions_in_comments(obj)
        exclude = mentions + [self.request.user.id]
        self.create_web_notifications_for_comment(obj, exclude)

        self.send_notifications(obj)
        super().post_save(obj, created)

    def pre_delete(self, obj):
        self.send_notifications(obj)
        super().pre_delete(obj)

    def create_web_notifications_for_comment(self, obj, exclude: list=None):
        if "comment" in self.request.DATA:
            watchers = [
                watcher_id for watcher_id in obj.watchers
                if watcher_id not in exclude
            ]

            signal_comment.send(sender=self.__class__,
                                user=self.request.user,
                                obj=obj,
                                watchers=watchers)

    def create_web_notifications_for_added_watchers(self, obj):
        if not hasattr(obj, "watchers"):
            return

        new_watchers = [
            watcher_id for watcher_id in obj.watchers
            if watcher_id not in self._old_watchers
            and watcher_id != self.request.user.id
        ]
        signal_watchers_added.send(sender=self.__class__,
                                   user=self.request.user,
                                   obj=obj,
                                   new_watchers=new_watchers)

    def create_web_notifications_for_mentioned_users(self, obj):
        """
        Detect and notify mentioned users
        """
        submitted_mentions = self._get_submitted_mentions(obj)
        new_mentions = list(set(submitted_mentions) - set(self._old_mentions))
        if new_mentions:
            signal_mentions.send(sender=self.__class__,
                                 user=self.request.user,
                                 obj=obj,
                                 mentions=new_mentions)

    def create_web_notifications_for_mentions_in_comments(self, obj):
        """
        Detect and notify mentioned users
        """
        new_mentions_in_comment = self._get_mentions_in_comment(obj)
        if new_mentions_in_comment:
            signal_comment_mentions.send(sender=self.__class__,
                                         user=self.request.user,
                                         obj=obj,
                                         mentions=new_mentions_in_comment)

        return [user.id for user in new_mentions_in_comment]

    def _get_submitted_mentions(self, obj):
        mention_fields = ['description', 'content']
        new_mentions = []
        for field_name in mention_fields:
            if not hasattr(obj, field_name) or not hasattr(obj, "get_project"):
                continue
            value = self.request.DATA.get(field_name)
            if not value:
                continue
            new_mentions += services.get_mentions(obj.get_project(), value)

        return new_mentions

    def _get_mentions_in_comment(self, obj):
        comment = self.request.DATA.get('comment')
        if not comment or not hasattr(obj, "get_project"):
            return []
        return services.get_mentions(obj.get_project(), comment)


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


class WatchedResourceSerializer(serializers.LightSerializer):
    is_watcher = MethodField()
    total_watchers = MethodField()

    def get_is_watcher(self, obj):
        # The "is_watcher" attribute is attached in the get_queryset of the viewset.
        if "request" in self.context:
            user = self.context["request"].user
            return user.is_authenticated and getattr(obj, "is_watcher", False)

        return False

    def get_total_watchers(self, obj):
        # The "total_watchers" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "total_watchers", 0) or 0


class EditableWatchedResourceSerializer(serializers.ModelSerializer):
    watchers = WatchersField(required=False)

    def restore_object(self, attrs, instance=None):
        # watchers is not a field from the model but can be attached in the get_queryset of the viewset.
        # If that's the case we need to remove it before calling the super method
        self.fields.pop("watchers", None)
        self.validate_watchers(attrs, "watchers")
        new_watcher_ids = attrs.pop("watchers", None)
        obj = super(EditableWatchedResourceSerializer, self).restore_object(attrs, instance)

        # A partial update can exclude the watchers field or if the new instance can still not be saved
        if instance is None or new_watcher_ids is None:
            return obj

        new_watcher_ids = set(new_watcher_ids)
        old_watcher_ids = set(obj.get_watchers().values_list("id", flat=True))
        adding_watcher_ids = list(new_watcher_ids.difference(old_watcher_ids))
        removing_watcher_ids = list(old_watcher_ids.difference(new_watcher_ids))

        adding_users = get_user_model().objects.filter(id__in=adding_watcher_ids)
        removing_users = get_user_model().objects.filter(id__in=removing_watcher_ids)
        for user in adding_users:
            services.add_watcher(obj, user)

        for user in removing_users:
            services.remove_watcher(obj, user)

        obj.watchers = obj.get_watchers()

        return obj

    def to_native(self, obj):
        # if watchers wasn't attached via the get_queryset of the viewset we need to manually add it
        if obj is not None:
            if not hasattr(obj, "watchers"):
                obj.watchers = [user.id for user in obj.get_watchers()]

            request = self.context.get("request", None)
            user = request.user if request else None
            if user and user.is_authenticated:
                obj.is_watcher = user.id in obj.watchers

        return super(WatchedResourceSerializer, self).to_native(obj)

    def save(self, **kwargs):
        obj = super(EditableWatchedResourceSerializer, self).save(**kwargs)
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
        resource = get_object_or_error(self.resource_model, request.user, pk=resource_id)

        self.check_permissions(request, 'retrieve', resource)

        try:
            self.object = resource.get_watchers().get(pk=pk)
        except ObjectDoesNotExist:  # or User.DoesNotExist
            return response.NotFound()

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    def list(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_error(self.resource_model, request.user, pk=resource_id)

        self.check_permissions(request, 'list', resource)

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        resource = self.resource_model.objects.get(pk=self.kwargs.get("resource_id"))
        return resource.get_watchers()


class AssignedToSignalMixin:
    _old_assigned_to = None

    def pre_save(self, obj):
        if obj.id:
            self._old_assigned_to = self.get_object().assigned_to
        super().pre_save(obj)

    def post_save(self, obj, created=False):
        if obj.assigned_to and obj.assigned_to != self._old_assigned_to \
                and self.request.user != obj.assigned_to:
            signal_assigned_to.send(sender=self.__class__,
                                    user=self.request.user,
                                    obj=obj)
        super().post_save(obj, created)


class AssignedUsersSignalMixin:
    def update(self, request, *args, **kwargs):
        if not request.DATA.get('assigned_users'):
            return super().update(request, *args, **kwargs)

        if not self.object:
            self.object = self.get_object_or_none()
        obj = self.object

        old_assigned_users = [user for user in obj.assigned_users.all()].copy()
        old_assigned_to = obj.assigned_to if obj.assigned_to else None

        result = super().update(request, *args, **kwargs)

        new_assigned_users = [
            user for user in result.data.get('assigned_users', [])
            if user not in old_assigned_users
            and user != old_assigned_to
            and user != self.request.user
        ] if 200 <= result.status_code < 300 else []

        if len(new_assigned_users):
            signal_assigned_users.send(sender=self.__class__,
                                       user=self.request.user,
                                       obj=obj,
                                       new_assigned_users=new_assigned_users)
        return result
