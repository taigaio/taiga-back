from contextlib import closing
from django.db import connection

def _get_issues_tags(project):
    extra_sql = ("select unnest(unpickle(tags)) as tagname "
                 "from issues_issue where project_id = %s "
                 "group by unnest(unpickle(tags)) "
                 "order by tagname asc")

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return set([x[0] for x in rows])

def _get_stories_tags(project):
    extra_sql = ("select unnest(unpickle(tags)) as tagname, count(unnest(unpickle(tags))) "
                 "from userstories_userstory where project_id = %s "
                 "group by unnest(unpickle(tags)) "
                 "order by tagname asc")

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return set([x[0] for x in rows])

def get_all_tags(project):
    result = set()
    result.update(_get_issues_tags(project))
    result.update(_get_stories_tags(project))
    return sorted(result)
