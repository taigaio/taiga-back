# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
from django.conf import settings
from taiga.base.utils.db import to_tsquery

MAX_RESULTS = getattr(settings, "SEARCHES_MAX_RESULTS", 150)


def search_user_stories(project, text):
    model_cls = apps.get_model("userstories", "UserStory")
    where_clause = ("to_tsvector('english_nostop', coalesce(userstories_userstory.subject) || ' ' || "
                                "coalesce(userstories_userstory.ref) || ' ' || "
                                "coalesce(userstories_userstory.description, '')) "
                    "@@ to_tsquery('english_nostop', %s)")

    if text:
        return (model_cls.objects.extra(where=[where_clause], params=[to_tsquery(text)])
                                 .filter(project_id=project.pk)[:MAX_RESULTS])

    return model_cls.objects.filter(project_id=project.pk)[:MAX_RESULTS]


def search_tasks(project, text):
    model_cls = apps.get_model("tasks", "Task")
    where_clause = ("to_tsvector('english_nostop', coalesce(tasks_task.subject, '') || ' ' || "
                    "coalesce(tasks_task.ref) || ' ' || "
                    "coalesce(tasks_task.description, '')) @@ to_tsquery('english_nostop', %s)")

    if text:
        return (model_cls.objects.extra(where=[where_clause], params=[to_tsquery(text)])
                                 .filter(project_id=project.pk)[:MAX_RESULTS])

    return model_cls.objects.filter(project_id=project.pk)[:MAX_RESULTS]


def search_issues(project, text):
    model_cls = apps.get_model("issues", "Issue")
    where_clause = ("to_tsvector('english_nostop', coalesce(issues_issue.subject) || ' ' || "
                    "coalesce(issues_issue.ref) || ' ' || "
                    "coalesce(issues_issue.description, '')) @@ to_tsquery('english_nostop', %s)")

    if text:
        return (model_cls.objects.extra(where=[where_clause], params=[to_tsquery(text)])
                                 .filter(project_id=project.pk)[:MAX_RESULTS])

    return model_cls.objects.filter(project_id=project.pk)[:MAX_RESULTS]


def search_wiki_pages(project, text):
    model_cls = apps.get_model("wiki", "WikiPage")
    where_clause = ("to_tsvector('english_nostop', coalesce(wiki_wikipage.slug) || ' ' || "
                                "coalesce(wiki_wikipage.content, '')) "
                    "@@ to_tsquery('english_nostop', %s)")

    if text:
        return (model_cls.objects.extra(where=[where_clause], params=[to_tsquery(text)])
                                 .filter(project_id=project.pk)[:MAX_RESULTS])

    return model_cls.objects.filter(project_id=project.pk)[:MAX_RESULTS]
