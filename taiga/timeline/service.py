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

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.db.models import Q
from django.db.models.query import QuerySet

from functools import partial, wraps

from taiga.base.utils.db import get_typename_for_model_class
from taiga.celery import app

_timeline_impl_map = {}


def _get_impl_key_from_model(model: Model, event_type: str):
    if issubclass(model, Model):
        typename = get_typename_for_model_class(model)
        return _get_impl_key_from_typename(typename, event_type)
    raise Exception("Not valid model parameter")


def _get_impl_key_from_typename(typename: str, event_type: str):
    if isinstance(typename, str):
        return "{0}.{1}".format(typename, event_type)
    raise Exception("Not valid typename parameter")


def build_user_namespace(user: object):
    return "{0}:{1}".format("user", user.id)


def build_project_namespace(project: object):
    return "{0}:{1}".format("project", project.id)


def _add_to_object_timeline(obj: object, instance: object, event_type: str, created_datetime: object,
                            namespace: str="default", extra_data: dict={}):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    from .models import Timeline
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    project = None
    if hasattr(instance, "project"):
        project = instance.project

    Timeline.objects.create(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        project=project,
        data=impl(instance, extra_data=extra_data),
        data_content_type=ContentType.objects.get_for_model(instance.__class__),
        created=created_datetime,
    )


def _add_to_objects_timeline(objects, instance: object, event_type: str, created_datetime: object,
                             namespace: str="default", extra_data: dict={}):
    for obj in objects:
        _add_to_object_timeline(obj, instance, event_type, created_datetime, namespace, extra_data)


def _push_to_timeline(objects, instance: object, event_type: str, created_datetime: object,
                      namespace: str="default", extra_data: dict={}):
    if isinstance(objects, Model):
        _add_to_object_timeline(objects, instance, event_type, created_datetime, namespace, extra_data)
    elif isinstance(objects, QuerySet) or isinstance(objects, list):
        _add_to_objects_timeline(objects, instance, event_type, created_datetime, namespace, extra_data)
    else:
        raise Exception("Invalid objects parameter")


@app.task
def push_to_timelines(project_id, user_id, obj_app_label, obj_model_name, obj_id, event_type,
                      created_datetime, extra_data={}):

    ObjModel = apps.get_model(obj_app_label, obj_model_name)
    try:
        obj = ObjModel.objects.get(id=obj_id)
    except ObjModel.DoesNotExist:
        return

    try:
        user = get_user_model().objects.get(id=user_id)
    except get_user_model().DoesNotExist:
        return

    if project_id is not None:
        # Actions related with a project

        projectModel = apps.get_model("projects", "Project")
        try:
            project = projectModel.objects.get(id=project_id)
        except projectModel.DoesNotExist:
            return

        # Project timeline
        _push_to_timeline(project, obj, event_type, created_datetime,
                          namespace=build_project_namespace(project),
                          extra_data=extra_data)

        project.refresh_totals()

        if hasattr(obj, "get_related_people"):
            related_people = obj.get_related_people()

            _push_to_timeline(related_people, obj, event_type, created_datetime,
                              namespace=build_user_namespace(user),
                              extra_data=extra_data)
    else:
        # Actions not related with a project
        # - Me
        _push_to_timeline(user, obj, event_type, created_datetime,
                          namespace=build_user_namespace(user),
                          extra_data=extra_data)


def get_timeline(obj, namespace=None):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    from .models import Timeline

    ct = ContentType.objects.get_for_model(obj.__class__)
    timeline = Timeline.objects.filter(content_type=ct, object_id=obj.pk)
    if namespace is not None:
        timeline = timeline.filter(namespace=namespace)

    timeline = timeline.order_by("-created", "-id")
    return timeline


def filter_timeline_for_user(timeline, user):
    # Superusers can see everything
    if user.is_superuser:
        return timeline

    # Filtering entities from public projects or entities without project
    tl_filter = Q(project__is_private=False) | Q(project=None)

    # Filtering private project with some public parts
    content_types = {
        "view_project": ContentType.objects.get_by_natural_key("projects", "project"),
        "view_milestones": ContentType.objects.get_by_natural_key("milestones", "milestone"),
        "view_epics": ContentType.objects.get_by_natural_key("epics", "epic"),
        "view_us": ContentType.objects.get_by_natural_key("userstories", "userstory"),
        "view_tasks": ContentType.objects.get_by_natural_key("tasks", "task"),
        "view_issues": ContentType.objects.get_by_natural_key("issues", "issue"),
        "view_wiki_pages": ContentType.objects.get_by_natural_key("wiki", "wikipage"),
        "view_wiki_links": ContentType.objects.get_by_natural_key("wiki", "wikilink"),
    }

    for content_type_key, content_type in content_types.items():
        tl_filter |= Q(project__is_private=True,
                       project__anon_permissions__contains=[content_type_key],
                       data_content_type=content_type)

    # There is no specific permission for seeing new memberships
    membership_content_type = ContentType.objects.get_by_natural_key(app_label="projects", model="membership")
    tl_filter |= Q(project__is_private=True,
                   project__anon_permissions__contains=["view_project"],
                   data_content_type=membership_content_type)

    # Filtering private projects where user is member
    if not user.is_anonymous():
        for membership in user.cached_memberships:
            # Admin roles can see everything in a project
            if membership.is_admin:
                tl_filter |= Q(project=membership.project)
            else:
                data_content_types = list(filter(None, [content_types.get(a, None) for a in
                                                        membership.role.permissions]))
                data_content_types.append(membership_content_type)
                tl_filter |= Q(project=membership.project, data_content_type__in=data_content_types)

    timeline = timeline.filter(tl_filter)
    return timeline


def get_profile_timeline(user, accessing_user=None):
    timeline = get_timeline(user)
    if accessing_user is not None:
        timeline = filter_timeline_for_user(timeline, accessing_user)
    return timeline


def get_user_timeline(user, accessing_user=None):
    namespace = build_user_namespace(user)
    timeline = get_timeline(user, namespace)
    if accessing_user is not None:
        timeline = filter_timeline_for_user(timeline, accessing_user)
    return timeline


def get_project_timeline(project, accessing_user=None):
    namespace = build_project_namespace(project)
    timeline = get_timeline(project, namespace)
    if accessing_user is not None:
        timeline = filter_timeline_for_user(timeline, accessing_user)
    return timeline


def register_timeline_implementation(typename: str, event_type: str, fn=None):
    assert isinstance(typename, str), "typename must be a string"
    assert isinstance(event_type, str), "event_type must be a string"

    if fn is None:
        return partial(register_timeline_implementation, typename, event_type)

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    key = _get_impl_key_from_typename(typename, event_type)

    _timeline_impl_map[key] = _wrapper
    return _wrapper


def extract_project_info(instance):
    return {
        "id": instance.pk,
        "slug": instance.slug,
        "name": instance.name,
        "description": instance.description,
    }


def extract_user_info(instance):
    return {
        "id": instance.pk
    }


def extract_milestone_info(instance):
    return {
        "id": instance.pk,
        "slug": instance.slug,
        "name": instance.name,
    }


def extract_epic_info(instance):
    return {
        "id": instance.pk,
        "ref": instance.ref,
        "subject": instance.subject,
    }


def extract_userstory_info(instance, include_project=False):
    userstory_info = {
        "id": instance.pk,
        "ref": instance.ref,
        "subject": instance.subject,
    }

    if include_project:
        userstory_info["project"] = extract_project_info(instance.project)

    return userstory_info


def extract_related_userstory_info(instance):
    return {
        "id": instance.pk,
        "subject": instance.user_story.subject
    }


def extract_issue_info(instance):
    return {
        "id": instance.pk,
        "ref": instance.ref,
        "subject": instance.subject,
    }


def extract_task_info(instance):
    return {
        "id": instance.pk,
        "ref": instance.ref,
        "subject": instance.subject,
    }


def extract_wiki_page_info(instance):
    return {
        "id": instance.pk,
        "slug": instance.slug,
    }


def extract_role_info(instance):
    return {
        "id": instance.pk,
        "name": instance.name,
    }
