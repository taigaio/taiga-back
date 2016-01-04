# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from django.utils.translation import ugettext as _

from taiga.projects.models import Membership

from . import serializers
from . import service


class TaigaImportError(Exception):
    def __init__(self, message):
        self.message = message


def store_milestones(project, data):
    results = []
    for milestone_data in data.get("milestones", []):
        milestone = service.store_milestone(project, milestone_data)
        results.append(milestone)
    return results


def store_tasks(project, data):
    results = []
    for task in data.get("tasks", []):
        task = service.store_task(project, task)
        results.append(task)
    return results


def store_wiki_pages(project, data):
    results = []
    for wiki_page in data.get("wiki_pages", []):
        results.append(service.store_wiki_page(project, wiki_page))
    return results


def store_wiki_links(project, data):
    results = []
    for wiki_link in data.get("wiki_links", []):
        results.append(service.store_wiki_link(project, wiki_link))
    return results


def store_user_stories(project, data):
    results = []
    for userstory in data.get("user_stories", []):
        us = service.store_user_story(project, userstory)
        results.append(us)
    return results


def store_timeline_entries(project, data):
    results = []
    for timeline in data.get("timeline", []):
        tl = service.store_timeline_entry(project, timeline)
        results.append(tl)
    return results


def store_issues(project, data):
    issues = []
    for issue in data.get("issues", []):
        issues.append(service.store_issue(project, issue))
    return issues


def store_tags_colors(project, data):
    project.tags_colors = data.get("tags_colors", [])
    project.save()
    return None


def dict_to_project(data, owner=None):
    if owner:
        data["owner"] = owner

    project_serialized = service.store_project(data)

    if not project_serialized:
        raise TaigaImportError(_("error importing project data"))

    proj = project_serialized.object

    service.store_choices(proj, data, "points", serializers.PointsExportSerializer)
    service.store_choices(proj, data, "issue_types", serializers.IssueTypeExportSerializer)
    service.store_choices(proj, data, "issue_statuses", serializers.IssueStatusExportSerializer)
    service.store_choices(proj, data, "us_statuses", serializers.UserStoryStatusExportSerializer)
    service.store_choices(proj, data, "task_statuses", serializers.TaskStatusExportSerializer)
    service.store_choices(proj, data, "priorities", serializers.PriorityExportSerializer)
    service.store_choices(proj, data, "severities", serializers.SeverityExportSerializer)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing lists of project attributes"))

    service.store_default_choices(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing default project attributes values"))

    service.store_custom_attributes(proj, data, "userstorycustomattributes",
                                    serializers.UserStoryCustomAttributeExportSerializer)
    service.store_custom_attributes(proj, data, "taskcustomattributes",
                                    serializers.TaskCustomAttributeExportSerializer)
    service.store_custom_attributes(proj, data, "issuecustomattributes",
                                    serializers.IssueCustomAttributeExportSerializer)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing custom attributes"))

    service.store_roles(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing roles"))

    service.store_memberships(proj, data)

    if proj.memberships.filter(user=proj.owner).count() == 0:
        if proj.roles.all().count() > 0:
            Membership.objects.create(
                project=proj,
                email=proj.owner.email,
                user=proj.owner,
                role=proj.roles.all().first(),
                is_owner=True
            )

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing memberships"))

    store_milestones(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing sprints"))

    store_wiki_pages(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing wiki pages"))

    store_wiki_links(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing wiki links"))

    store_issues(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing issues"))

    store_user_stories(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing user stories"))

    store_tasks(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing tasks"))

    store_tags_colors(proj, data)

    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing tags"))

    store_timeline_entries(proj, data)
    if service.get_errors(clear=False):
        raise TaigaImportError(_("error importing timelines"))

    return proj
