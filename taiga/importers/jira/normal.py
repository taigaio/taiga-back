# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from collections import OrderedDict

from django.template.defaultfilters import slugify
from taiga.projects.references.models import recalc_reference_counter
from taiga.projects.models import Project, ProjectTemplate, Points
from taiga.projects.userstories.models import UserStory, RolePoints
from taiga.projects.tasks.models import Task
from taiga.projects.issues.models import Issue
from taiga.projects.epics.models import Epic, RelatedUserStory
from taiga.projects.history.services import take_snapshot
from taiga.timeline.rebuilder import rebuild_timeline
from taiga.timeline.models import Timeline
from .common import JiraImporterCommon
from taiga.importers import services as import_service


class JiraNormalImporter(JiraImporterCommon):
    def list_projects(self):
        return [{"id": project['id'],
                 "name": project['name'],
                 "description": project['description'],
                 "is_private": True,
                 "importer_type": "normal"} for project in self._client.get('/project', {"expand": "description"})]

    def list_issue_types(self, project_id):
        statuses = self._client.get("/project/{}/statuses".format(project_id))
        return statuses

    def import_project(self, project_id, options):
        self.resolve_user_bindings(options)
        project = self._import_project_data(project_id, options)
        self._import_user_stories_data(project_id, project, options)
        self._import_epics_data(project_id, project, options)
        self._link_epics_with_user_stories(project_id, project, options)
        self._import_issues_data(project_id, project, options)
        self._cleanup(project, options)
        Timeline.objects.filter(project=project).delete()
        rebuild_timeline(None, None, project.id)
        recalc_reference_counter(project)
        return project

    def _import_project_data(self, project_id, options):
        project = self._client.get("/project/{}".format(project_id))
        project_template = ProjectTemplate.objects.get(slug=options['template'])

        epic_statuses = OrderedDict()
        for issue_type in options.get('types_bindings', {}).get("epic", []):
            for status in issue_type['statuses']:
                epic_statuses[status['name']] = status

        us_statuses = OrderedDict()
        for issue_type in options.get('types_bindings', {}).get("us", []):
            for status in issue_type['statuses']:
                us_statuses[status['name']] = status

        task_statuses = OrderedDict()
        for issue_type in options.get('types_bindings', {}).get("task", []):
            for status in issue_type['statuses']:
                task_statuses[status['name']] = status

        issue_statuses = OrderedDict()
        for issue_type in options.get('types_bindings', {}).get("issue", []):
            for status in issue_type['statuses']:
                issue_statuses[status['name']] = status

        counter = 0
        if epic_statuses:
            project_template.epic_statuses = []
            project_template.is_epics_activated = True
        for epic_status in epic_statuses.values():
            project_template.epic_statuses.append({
                "name": epic_status['name'],
                "slug": slugify(epic_status['name']),
                "is_closed": False,
                "color": "#999999",
                "order": counter,
            })
            counter += 1
        if epic_statuses:
            project_template.default_options["epic_status"] = list(epic_statuses.values())[0]['name']

        project_template.points = [{
            "value": None,
            "name": "?",
            "order": 0,
        }]

        main_permissions = project_template.roles[0]['permissions']
        project_template.roles = [{
            "name": "Main",
            "slug": "main",
            "computable": True,
            "permissions": main_permissions,
            "order": 70,
        }]

        counter = 0
        if us_statuses:
            project_template.us_statuses = []
        for us_status in us_statuses.values():
            project_template.us_statuses.append({
                "name": us_status['name'],
                "slug": slugify(us_status['name']),
                "is_closed": False,
                "is_archived": False,
                "color": "#999999",
                "wip_limit": None,
                "order": counter,
            })
            counter += 1
        if us_statuses:
            project_template.default_options["us_status"] = list(us_statuses.values())[0]['name']

        counter = 0
        if task_statuses:
            project_template.task_statuses = []
        for task_status in task_statuses.values():
            project_template.task_statuses.append({
                "name": task_status['name'],
                "slug": slugify(task_status['name']),
                "is_closed": False,
                "color": "#999999",
                "order": counter,
            })
            counter += 1
        if task_statuses:
            project_template.default_options["task_status"] = list(task_statuses.values())[0]['name']

        counter = 0
        if issue_statuses:
            project_template.issue_statuses = []
        for issue_status in issue_statuses.values():
            project_template.issue_statuses.append({
                "name": issue_status['name'],
                "slug": slugify(issue_status['name']),
                "is_closed": False,
                "color": "#999999",
                "order": counter,
            })
            counter += 1
        if issue_statuses:
            project_template.default_options["issue_status"] = list(issue_statuses.values())[0]['name']


        main_permissions = project_template.roles[0]['permissions']
        project_template.roles = [{
            "name": "Main",
            "slug": "main",
            "computable": True,
            "permissions": main_permissions,
            "order": 70,
        }]

        project = Project.objects.create(
            name=options.get('name', None) or project['name'],
            description=options.get('description', None) or project.get('description', ''),
            owner=self._user,
            creation_template=project_template,
            is_private=options.get('is_private', False),
        )

        self._create_custom_fields(project)
        import_service.create_memberships(options.get('users_bindings', {}), project, self._user, "main")

        return project

    def _import_user_stories_data(self, project_id, project, options):
        users_bindings = options.get('users_bindings', {})

        types = options.get('types_bindings', {}).get("us", [])
        for issue_type in types:
            counter = 0
            offset = 0
            while True:
                issues = self._client.get("/search", {
                    "jql": "project={} AND issuetype={}".format(project_id, issue_type['id']),
                    "startAt": offset,
                    "fields": "*all",
                    "expand": "changelog,attachment",
                })
                offset += issues['maxResults']

                for issue in issues['issues']:
                    issue['fields']['issuelinks'] += self._client.get("/issue/{}/remotelink".format(issue['key']))
                    assigned_to = users_bindings.get(issue['fields']['assignee']['key'] if issue['fields']['assignee'] else None, None)
                    owner = users_bindings.get(issue['fields']['creator']['key'] if issue['fields']['creator'] else None, self._user)

                    external_reference = None
                    if options.get('keep_external_reference', False) and 'url' in issue['fields']:
                        external_reference = ["jira", issue['fields']['url']]


                    us = UserStory.objects.create(
                        project=project,
                        owner=owner,
                        assigned_to=assigned_to,
                        status=project.us_statuses.get(name=issue['fields']['status']['name']),
                        kanban_order=counter,
                        sprint_order=counter,
                        backlog_order=counter,
                        subject=issue['fields']['summary'],
                        description=issue['fields']['description'] or '',
                        tags=issue['fields']['labels'],
                        external_reference=external_reference,
                    )

                    points_value = issue['fields'].get(self.greenhopper_fields.get('points', None), None)
                    if points_value:
                        (points, _) = Points.objects.get_or_create(
                            project=project,
                            value=points_value,
                            defaults={
                                "name": str(points_value),
                                "order": points_value,
                            }
                        )
                        RolePoints.objects.filter(user_story=us, role__slug="main").update(points_id=points.id)
                    else:
                        points = Points.objects.get(project=project, value__isnull=True)
                        RolePoints.objects.filter(user_story=us, role__slug="main").update(points_id=points.id)

                    self._import_to_custom_fields(us, issue, options)

                    us.ref = issue['key'].split("-")[1]
                    UserStory.objects.filter(id=us.id).update(
                        ref=us.ref,
                        modified_date=issue['fields']['updated'],
                        created_date=issue['fields']['created']
                    )
                    take_snapshot(us, comment="", user=None, delete=False)
                    self._import_subtasks(project_id, project, us, issue, options)
                    self._import_comments(us, issue, options)
                    self._import_attachments(us, issue, options)
                    self._import_changelog(project, us, issue, options)
                    counter += 1

                if len(issues['issues']) < issues['maxResults']:
                    break

    def _import_subtasks(self, project_id, project, us, issue, options):
        users_bindings = options.get('users_bindings', {})

        if len(issue['fields']['subtasks']) == 0:
            return

        counter = 0
        offset = 0
        while True:
            issues = self._client.get("/search", {
                "jql": "parent={}".format(issue['key']),
                "startAt": offset,
                "fields": "*all",
                "expand": "changelog,attachment",
            })
            offset += issues['maxResults']

            for issue in issues['issues']:
                issue['fields']['issuelinks'] += self._client.get("/issue/{}/remotelink".format(issue['key']))
                assigned_to = users_bindings.get(issue['fields']['assignee']['key'] if issue['fields']['assignee'] else None, None)
                owner = users_bindings.get(issue['fields']['creator']['key'] if issue['fields']['creator'] else None, self._user)

                external_reference = None
                if options.get('keep_external_reference', False) and 'url' in issue['fields']:
                    external_reference = ["jira", issue['fields']['url']]

                task = Task.objects.create(
                    user_story=us,
                    project=project,
                    owner=owner,
                    assigned_to=assigned_to,
                    status=project.task_statuses.get(name=issue['fields']['status']['name']),
                    subject=issue['fields']['summary'],
                    description=issue['fields']['description'] or '',
                    tags=issue['fields']['labels'],
                    external_reference=external_reference,
                )

                self._import_to_custom_fields(task, issue, options)

                task.ref = issue['key'].split("-")[1]
                Task.objects.filter(id=task.id).update(
                    ref=task.ref,
                    modified_date=issue['fields']['updated'],
                    created_date=issue['fields']['created']
                )
                take_snapshot(task, comment="", user=None, delete=False)
                for subtask in issue['fields']['subtasks']:
                    print("WARNING: Ignoring subtask {} because parent isn't a User Story".format(subtask['key']))
                self._import_comments(task, issue, options)
                self._import_attachments(task, issue, options)
                self._import_changelog(project, task, issue, options)
                counter += 1
            if len(issues['issues']) < issues['maxResults']:
                break

    def _import_issues_data(self, project_id, project, options):
        users_bindings = options.get('users_bindings', {})

        types = options.get('types_bindings', {}).get("issue", [])
        for issue_type in types:
            counter = 0
            offset = 0
            while True:
                issues = self._client.get("/search", {
                    "jql": "project={} AND issuetype={}".format(project_id, issue_type['id']),
                    "startAt": offset,
                    "fields": "*all",
                    "expand": "changelog,attachment",
                })
                offset += issues['maxResults']

                for issue in issues['issues']:
                    issue['fields']['issuelinks'] += self._client.get("/issue/{}/remotelink".format(issue['key']))
                    assigned_to = users_bindings.get(issue['fields']['assignee']['key'] if issue['fields']['assignee'] else None, None)
                    owner = users_bindings.get(issue['fields']['creator']['key'] if issue['fields']['creator'] else None, self._user)

                    external_reference = None
                    if options.get('keep_external_reference', False) and 'url' in issue['fields']:
                        external_reference = ["jira", issue['fields']['url']]

                    taiga_issue = Issue.objects.create(
                        project=project,
                        owner=owner,
                        assigned_to=assigned_to,
                        status=project.issue_statuses.get(name=issue['fields']['status']['name']),
                        subject=issue['fields']['summary'],
                        description=issue['fields']['description'] or '',
                        tags=issue['fields']['labels'],
                        external_reference=external_reference,
                    )

                    self._import_to_custom_fields(taiga_issue, issue, options)

                    taiga_issue.ref = issue['key'].split("-")[1]
                    Issue.objects.filter(id=taiga_issue.id).update(
                        ref=taiga_issue.ref,
                        modified_date=issue['fields']['updated'],
                        created_date=issue['fields']['created']
                    )
                    take_snapshot(taiga_issue, comment="", user=None, delete=False)
                    for subtask in issue['fields']['subtasks']:
                        print("WARNING: Ignoring subtask {} because parent isn't a User Story".format(subtask['key']))
                    self._import_comments(taiga_issue, issue, options)
                    self._import_attachments(taiga_issue, issue, options)
                    self._import_changelog(project, taiga_issue, issue, options)
                    counter += 1

                if len(issues['issues']) < issues['maxResults']:
                    break

    def _import_epics_data(self, project_id, project, options):
        users_bindings = options.get('users_bindings', {})

        types = options.get('types_bindings', {}).get("epic", [])
        for issue_type in types:
            counter = 0
            offset = 0
            while True:
                issues = self._client.get("/search", {
                    "jql": "project={} AND issuetype={}".format(project_id, issue_type['id']),
                    "startAt": offset,
                    "fields": "*all",
                    "expand": "changelog,attachment",
                })
                offset += issues['maxResults']

                for issue in issues['issues']:
                    issue['fields']['issuelinks'] += self._client.get("/issue/{}/remotelink".format(issue['key']))
                    assigned_to = users_bindings.get(issue['fields']['assignee']['key'] if issue['fields']['assignee'] else None, None)
                    owner = users_bindings.get(issue['fields']['creator']['key'] if issue['fields']['creator'] else None, self._user)

                    external_reference = None
                    if options.get('keep_external_reference', False) and 'url' in issue['fields']:
                        external_reference = ["jira", issue['fields']['url']]

                    epic = Epic.objects.create(
                        project=project,
                        owner=owner,
                        assigned_to=assigned_to,
                        status=project.epic_statuses.get(name=issue['fields']['status']['name']),
                        subject=issue['fields']['summary'],
                        description=issue['fields']['description'] or '',
                        epics_order=counter,
                        tags=issue['fields']['labels'],
                        external_reference=external_reference,
                    )

                    self._import_to_custom_fields(epic, issue, options)

                    epic.ref = issue['key'].split("-")[1]
                    Epic.objects.filter(id=epic.id).update(
                        ref=epic.ref,
                        modified_date=issue['fields']['updated'],
                        created_date=issue['fields']['created']
                    )
                    take_snapshot(epic, comment="", user=None, delete=False)
                    for subtask in issue['fields']['subtasks']:
                        print("WARNING: Ignoring subtask {} because parent isn't a User Story".format(subtask['key']))
                    self._import_comments(epic, issue, options)
                    self._import_attachments(epic, issue, options)
                    issue_with_changelog = self._client.get("/issue/{}".format(issue['key']), {
                        "expand": "changelog"
                    })
                    self._import_changelog(project, epic, issue_with_changelog, options)
                    counter += 1

                if len(issues['issues']) < issues['maxResults']:
                    break

    def _link_epics_with_user_stories(self, project_id, project, options):
        types = options.get('types_bindings', {}).get("us", [])
        for issue_type in types:
            offset = 0
            while True:
                issues = self._client.get("/search", {
                    "jql": "project={} AND issuetype={}".format(project_id, issue_type['id']),
                    "startAt": offset
                })
                offset += issues['maxResults']

                for issue in issues['issues']:
                    epic_key = issue['fields'][self.greenhopper_fields['link']]
                    if epic_key:
                        epic = project.epics.get(ref=int(epic_key.split("-")[1]))
                        us = project.user_stories.get(ref=int(issue['key'].split("-")[1]))
                        RelatedUserStory.objects.create(
                            user_story=us,
                            epic=epic,
                            order=1
                        )

                if len(issues['issues']) < issues['maxResults']:
                    break
