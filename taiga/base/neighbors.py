# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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
from collections import namedtuple

from django.db.models import Q


Neighbor = namedtuple("Neighbor", "left right")


def disjunction_filters(filters):
    """From a list of queryset filters, it returns a disjunction (OR) Q object.

    :param filters: List of filters where each item is a dict where the keys are the lookups and
    the values the values of those lookups.

    :return: :class:`django.db.models.Q` instance representing the disjunction of the filters.
    """
    result = Q()
    for filter in filters:
        result |= Q(**{lookup: value for lookup, value in filter.items()})
    return result


def get_attribute(obj, attr):
    """Finds `attr` in obj.

    :param obj: Object where to look for the attribute.
    :param attr: Attribute name as a string. It can be a Django lookup field such as
    `project__owner__name`, in which case it will look for `obj.project.owner.name`.

    :return: The attribute value.
    :raises: `AttributeError` if some attribute doesn't exist.
    """
    chunks = attr.lstrip("-").split("__")
    attr, chunks = chunks[0], chunks[1:]
    obj = value = getattr(obj, attr)
    for path in chunks:
        value = getattr(obj, path)
        obj = value

    return value


def transform_field_into_lookup(name, value, operator="", operator_if_desc=""):
    """From a field name and value, return a dict that may be used as a queryset filter.

    :param name: Field name as a string.
    :param value: Field value.
    :param operator: Operator to use in the lookup.
    :param operator_if_desc: If the field is reversed (a "-" in front) use this operator
    instead.

    :return: A dict that may be used as a queryset filter.
    """
    if name.startswith("-"):
        name = name[1:]
        operator = operator_if_desc
    lookup = "{}{}".format(name, operator)
    return {lookup: value}


def get_neighbors(obj, results_set=None):
    """Get the neighbors of a model instance.

    The neighbors are the objects that are at the left/right of `obj` in the results set.

    :param obj: The object you want to know its neighbors.
    :param results_set: Find the neighbors applying the constraints of this set (a Django queryset
        object).

    :return: Tuple `<left neighbor>, <right neighbor>`. Left and right neighbors can be `None`.
    """
    if results_set is None or results_set.count() == 0:
        results_set = type(obj).objects.get_queryset()
    try:
        left = _left_candidates(obj, results_set).reverse()[0]
    except IndexError:
        left = None
    try:
        right = _right_candidates(obj, results_set)[0]
    except IndexError:
        right = None

    return Neighbor(left, right)


def _get_candidates(obj, results_set, reverse=False):
    ordering = (results_set.query.order_by or []) + list(obj._meta.ordering)
    main_ordering, rest_ordering = ordering[0], ordering[1:]
    try:
        filters = obj.get_neighbors_additional_filters(results_set, ordering, reverse)
        if filters is None:
            raise AttributeError
    except AttributeError:
        filters = [order_field_as_filter(obj, main_ordering, reverse)]
        filters += [ordering_fields_as_filter(obj, main_ordering, rest_ordering, reverse)]

    return (results_set
            .filter(~Q(id=obj.id), disjunction_filters(filters))
            .distinct()
            .order_by(*ordering))
_left_candidates = partial(_get_candidates, reverse=True)
_right_candidates = partial(_get_candidates, reverse=False)


def order_field_as_filter(obj, order_field, reverse=None, operator=None):
    value = get_attribute(obj, order_field)
    if reverse is not None:
        if operator is None:
            operator = ("__gt", "__lt")
        operator = (operator[1], operator[0]) if reverse else operator
    else:
        operator = ()
    return transform_field_into_lookup(order_field, value, *operator)


def ordering_fields_as_filter(obj, main_order_field, ordering_fields, reverse=False):
    """Transform a list of ordering fields into a queryset filter."""
    filter = order_field_as_filter(obj, main_order_field)
    for field in ordering_fields:
        filter.update(order_field_as_filter(obj, field, reverse, ("__gte", "__lte")))
    return filter
