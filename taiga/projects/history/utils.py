# -*- coding: utf-8 -*-
from taiga.projects.history.services import get_typename_for_model_class


def attach_total_comments_to_queryset(queryset, as_field="total_comments"):
    """Attach a total comments counter to each object of the queryset.

    :param queryset: A Django projects queryset object.
    :param as_field: Attach the counter as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """
             SELECT COUNT(history_historyentry.id)
               FROM history_historyentry
              WHERE history_historyentry.key = CONCAT('{key_prefix}', {tbl}.id) AND
                    history_historyentry.comment is not null AND
                    history_historyentry.comment != ''
          """

    typename = get_typename_for_model_class(model)

    sql = sql.format(tbl=model._meta.db_table, key_prefix="{}:".format(typename))

    queryset = queryset.extra(select={as_field: sql})
    return queryset
