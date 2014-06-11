import re
from functools import partial

import six

from django.db import models
from django.utils.translation import ugettext_lazy as _

from djorm_pgarray.fields import TextArrayField

from picklefield.fields import PickledObjectField


class TaggedMixin(models.Model):
    pgtags = TextArrayField(default=None, verbose_name=_("tags"))
    tags = PickledObjectField(null=False, blank=True, verbose_name=_("tags"))

    class Meta:
        abstract = True


def get_queryset_table(queryset):
    """Return queryset model's table name"""
    return queryset.model._meta.db_table


def _filter_bin(queryset, value, operator):
    """tags <operator> <value>"""
    if not isinstance(value, str):
        value = ",".join(value)

    sql = "{table_name}.tags {operator} string_to_array(%s, ',')"
    where_clause = sql.format(table_name=get_queryset_table(queryset), operator=operator)
    queryset = queryset.extra(where=[where_clause], params=[value])
    return queryset
_filter_contains = partial(_filter_bin, operator="@>")
_filter_contained_by = partial(_filter_bin, operator="<@")
_filter_overlap = partial(_filter_bin, operator="&&")


def _filter_index(queryset, index, value):
    """tags[<index>] == <value>"""
    sql = "{table_name}.tags[{index}] = %s"
    where_clause = sql.format(table_name=get_queryset_table(queryset), index=index)
    queryset = queryset.extra(where=[where_clause], params=[value])
    return queryset


def _filter_len(queryset, value):
    """len(tags) == <value>"""
    sql = "array_length({table_name}.tags, 1) = %s"
    where_clause = sql.format(table_name=get_queryset_table(queryset))
    queryset = queryset.extra(where=[where_clause], params=[value])
    return queryset


def _filter_len_operator(queryset, value, operator):
    """len(tags) <operator> <value>"""
    operator = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<="}[operator]
    sql = "array_length({table_name}.tags, 1) {operator} %s"
    where_clause = sql.format(table_name=get_queryset_table(queryset), operator=operator)
    queryset = queryset.extra(where=[where_clause], params=[value])
    return queryset


def _filter_index_operator(queryset, value, operator):
    """tags[<operator>] == value"""
    index = int(operator) + 1
    sql = "{table_name}.tags[{index}] = %s"
    where_clause = sql.format(table_name=get_queryset_table(queryset), index=index)
    queryset = queryset.extra(where=[where_clause], params=[value])
    return queryset


def _tags_filter(**filters_map):
    filter_re = re.compile(r"""(?:(len__)(gte|lte|lt|gt)
                               |
                               (index__)(\d+))""", re.VERBOSE)

    def get_filter(filter_name, strict=False):
        return filters_map[filter_name] if strict else filters_map.get(filter_name)

    def get_filter_matching(filter_name):
        match = filter_re.search(filter_name)
        filter_name, operator = (group for group in match.groups() if group)
        return partial(get_filter(filter_name, strict=True), operator=operator)

    def tags_filter(model_or_qs, **filters):
        "Filter a queryset but adding support to filters that work with postgresql array fields"
        if hasattr(model_or_qs, "_meta"):
            qs = model_or_qs._default_manager.get_queryset()
        else:
            qs = model_or_qs

        for filter_name, filter_value in six.iteritems(filters):
            try:
                filter = get_filter(filter_name) or get_filter_matching(filter_name)
            except (LookupError, AttributeError):
                qs = qs.filter(**{filter_name: filter_value})
            else:
                qs = filter(queryset=qs, value=filter_value)
        return qs

    return tags_filter
filter = _tags_filter(contains=_filter_contains,
                      contained_by=_filter_contained_by,
                      overlap=_filter_overlap,
                      len=_filter_len,
                      len__=_filter_len_operator,
                      index__=_filter_index_operator)
