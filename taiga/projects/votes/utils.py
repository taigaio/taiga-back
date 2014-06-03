from django.db.models.loading import get_model


def attach_votescount_to_queryset(queryset, as_field="votes_count"):
    """Attach votes count to each object of the queryset.

    Because of laziness of vote objects creation, this makes much simpler and more efficient to
    access to voted-object number of votes.

    (The other way was to do it in the serializer with some try/except blocks and additional
    queries)

    :param queryset: A Django queryset object.
    :param as_field: Attach the votes-count as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql = ("SELECT coalesce(votes_votes.count, 0) FROM votes_votes "
           "WHERE votes_votes.content_type_id = {type_id} AND votes_votes.object_id = {tbl}.id")
    sql = sql.format(type_id=type.id, tbl=model._meta.db_table)
    qs = queryset.extra(select={as_field: sql})
    return qs
