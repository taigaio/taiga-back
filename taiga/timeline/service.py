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

from django.db.models import Model
from django.db.models.query import QuerySet
from functools import partial, wraps
from django.contrib.contenttypes.models import ContentType

from taiga.base.utils.db import get_typename_for_model_class

_timeline_impl_map = {}


def _get_impl_key_from_model(model:Model, event_type:str):
    if issubclass(model, Model):
        typename = get_typename_for_model_class(model)
        return _get_impl_key_from_typename(typename, event_type)
    raise Exception("Not valid model parameter")


def _get_impl_key_from_typename(typename:str, event_type:str):
    if isinstance(typename, str):
        return "{0}.{1}".format(typename, event_type)
    raise Exception("Not valid typename parameter")


def _get_class_implementation(model:Model, event_type:str):
    key = _get_impl_key_from_model(model, event_type)
    return _timeline_impl_map.get(key, None)


def _add_to_object_timeline(obj:object, instance:object, event_type:str, namespace:str="default", extra_data:dict={}):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    from .models import Timeline

    impl = _get_class_implementation(instance.__class__, event_type)
    Timeline.objects.create(
        content_object=obj,
        namespace=namespace,
        event_type=event_type,
        data=impl(instance, extra_data=extra_data)
    )


def _add_to_objects_timeline(objects, instance:object, event_type:str, namespace:str="default", extra_data:dict={}):
    for obj in objects:
        _add_to_object_timeline(obj, instance, event_type, namespace, extra_data)


def push_to_timeline(objects, instance:object, event_type:str, namespace:str="default", extra_data:dict={}):
    if isinstance(objects, Model):
        _add_to_object_timeline(objects, instance, event_type, namespace, extra_data)
    elif isinstance(objects, QuerySet) or isinstance(objects, list):
        _add_to_objects_timeline(objects, instance, event_type, namespace, extra_data)
    else:
        raise Exception("Invalid objects parameter")


def get_timeline(obj, namespace="default"):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    from .models import Timeline

    ct = ContentType.objects.get_for_model(obj.__class__)
    return Timeline.objects.filter(content_type=ct, object_id=obj.pk, namespace=namespace)


def register_timeline_implementation(typename:str, event_type:str, fn=None):
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
