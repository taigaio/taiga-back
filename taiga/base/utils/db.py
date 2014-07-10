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

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from . import functions


def get_typename_for_model_class(model:object, for_concrete_model=True) -> str:
    """
    Get typename for model instance.
    """
    if for_concrete_model:
        model = model._meta.concrete_model
    else:
        model = model._meta.proxy_for_model

    return "{0}.{1}".format(model._meta.app_label, model._meta.model_name)


def reload_attribute(model_instance, attr_name):
    """Fetch the stored value of a model instance attribute.

    :param model_instance: Model instance.
    :param attr_name: Attribute name to fetch.
    """
    qs = type(model_instance).objects.filter(id=model_instance.id)
    return qs.values_list(attr_name, flat=True)[0]


@transaction.atomic
def save_in_bulk(instances, callback=None, **save_options):
    """Save a list of model instances.

    :params callback: Callback to call after each save.
    :params save_options: Additional options to use when saving each instance.
    """
    if callback is None:
        callback = functions.identity

    for instance in instances:
        instance.save(**save_options)
        callback(instance)
