FILTER_TAGS_SQL = "unpickle({table}.tags) && %s"


def filter_by_tags(tags, queryset):
    """Filter a queryset of a model with pickled field named tags, by tags."""
    table_name = queryset.model._meta.db_table
    where_sql = FILTER_TAGS_SQL.format(table=table_name)

    return queryset.extra(where=[where_sql], params=[tags])
