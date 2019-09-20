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

import datetime
import requests
from urllib.parse import parse_qsl
from django.core.files.base import ContentFile

from taiga.projects.models import Project, ProjectTemplate
from taiga.projects.references.models import recalc_reference_counter
from taiga.projects.userstories.models import UserStory
from taiga.projects.issues.models import Issue
from taiga.projects.milestones.models import Milestone
from taiga.projects.history.services import take_snapshot
from taiga.projects.history.services import (make_diff_from_dicts,
                                             make_diff_values,
                                             make_key_from_model_object,
                                             get_typename_for_model_class,
                                             FrozenDiff)
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.choices import HistoryType
from taiga.timeline.rebuilder import rebuild_timeline
from taiga.timeline.models import Timeline
from taiga.users.models import User, AuthData

from taiga.importers.exceptions import InvalidAuthResult, FailedRequest
from taiga.importers import services as import_service


class GithubClient:
    def __init__(self, token):
        self.api_url = "https://api.github.com/{}"
        self.token = token

    def get(self, uri_path, query_params=None):
        headers = {
            "Content-Type": "application/json",
            "X-GitHub-Media-Type": "github.v3"
        }
        if self.token:
            headers['Authorization'] = 'token {}'.format(self.token)

        if query_params is None:
            query_params = {}

        if uri_path[0] == '/':
            uri_path = uri_path[1:]
        url = self.api_url.format(uri_path)

        response = requests.get(url, params=query_params, headers=headers)

        if response.status_code == 401:
            raise Exception("Unauthorized: %s at %s" % (response.text, url), response)
        if response.status_code != 200:
            raise Exception("Resource Unavailable: %s at %s" % (response.text, url), response)

        return response.json()


class GithubImporter:
    def __init__(self, user, token, import_closed_data=False):
        self._import_closed_data = import_closed_data
        self._user = user
        self._client = GithubClient(token)
        self._me = self._client.get("/user")

    def list_projects(self):
        projects = []
        page = 1
        while True:
            repos = self._client.get("/user/repos", {
                "sort": "full_name",
                "page": page,
                "per_page": 100
            })
            page += 1

            for repo in repos:
                projects.append({
                    "id": repo['full_name'],
                    "name": repo['full_name'],
                    "description": repo['description'],
                    "is_private": repo['private'],
                })

            if len(repos) < 100:
                break
        return projects

    def list_users(self, project_full_name):
        collaborators = self._client.get("/repos/{}/collaborators".format(project_full_name))
        collaborators = [self._client.get("/users/{}".format(u['login'])) for u in collaborators]
        return [{"id": u['id'],
                 "username": u['login'],
                 "full_name": u.get('name', u['login']),
                 "avatar": u.get('avatar_url', None),
                 "detected_user": self._get_user(u) } for u in collaborators]

    def _get_user(self, user, default=None):
        if not user:
            return default

        try:
            return AuthData.objects.get(key="github", value=user['id']).user
        except AuthData.DoesNotExist:
            pass

        try:
            return User.objects.get(email=user.get('email', "not-valid"))
        except User.DoesNotExist:
            pass

        return default

    def import_project(self, project_full_name, options={"keep_external_reference": False, "template": "kanban", "type": "user_stories"}):
        repo = self._client.get('/repos/{}'.format(project_full_name))
        project = self._import_project_data(repo, options)
        if options.get('type', None) == "user_stories":
            self._import_user_stories_data(project, repo, options)
        elif options.get('type', None) == "issues":
            self._import_issues_data(project, repo, options)
        self._import_comments(project, repo, options)
        self._import_history(project, repo, options)
        Timeline.objects.filter(project=project).delete()
        rebuild_timeline(None, None, project.id)
        recalc_reference_counter(project)
        return project

    def _import_project_data(self, repo, options):
        users_bindings = options.get('users_bindings', {})
        project_template = ProjectTemplate.objects.get(slug=options['template'])

        if options['type'] == "user_stories":
            project_template.us_statuses = []
            project_template.us_statuses.append({
                "name": "Open",
                "slug": "open",
                "is_closed": False,
                "is_archived": False,
                "color": "#ff8a84",
                "wip_limit": None,
                "order": 1,
            })
            project_template.us_statuses.append({
                "name": "Closed",
                "slug": "closed",
                "is_closed": True,
                "is_archived": False,
                "color": "#669900",
                "wip_limit": None,
                "order": 2,
            })
            project_template.default_options["us_status"] = "Open"
        elif options['type'] == "issues":
            project_template.issue_statuses = []
            project_template.issue_statuses.append({
                "name": "Open",
                "slug": "open",
                "is_closed": False,
                "color": "#ff8a84",
                "order": 1,
            })
            project_template.issue_statuses.append({
                "name": "Closed",
                "slug": "closed",
                "is_closed": True,
                "color": "#669900",
                "order": 2,
            })
            project_template.default_options["issue_status"] = "Open"

        project_template.roles.append({
            "name": "Github",
            "slug": "github",
            "computable": False,
            "permissions": project_template.roles[0]['permissions'],
            "order": 70,
        })

        tags_colors = []
        for label in self._client.get("/repos/{}/labels".format(repo['full_name'])):
            name = label['name'].lower()
            color = "#{}".format(label['color'])
            tags_colors.append([name, color])

        project = Project.objects.create(
            name=options.get('name', None) or repo['full_name'],
            description=options.get('description', None) or repo['description'],
            owner=self._user,
            tags_colors=tags_colors,
            creation_template=project_template,
            is_private=options.get('is_private', False),
        )

        if 'organization' in repo and repo['organization'].get('avatar_url', None):
            data = requests.get(repo['organization']['avatar_url'])
            project.logo.save("logo.png", ContentFile(data.content), save=True)

        import_service.create_memberships(options.get('users_bindings', {}), project, self._user, "github")

        for milestone in self._client.get("/repos/{}/milestones".format(repo['full_name'])):
            taiga_milestone = Milestone.objects.create(
                name=milestone['title'],
                owner=users_bindings.get(milestone.get('creator', {}).get('id', None), self._user),
                project=project,
                estimated_start=milestone['created_at'][:10],
                estimated_finish=milestone['due_on'][:10] if milestone['due_on'] else datetime.date(datetime.MAXYEAR, 12, 31),
            )
            Milestone.objects.filter(id=taiga_milestone.id).update(
                created_date=milestone['created_at'],
                modified_date=milestone['updated_at'],
            )
        return project

    def _import_user_stories_data(self, project, repo, options):
        users_bindings = options.get('users_bindings', {})

        page = 1
        while True:
            issues = self._client.get("/repos/{}/issues".format(repo['full_name']), {
                "state": "all",
                "sort": "created",
                "direction": "asc",
                "page": page,
                "per_page": 100
            })
            page += 1
            for issue in issues:
                tags = []
                for label in issue['labels']:
                    tags.append(label['name'].lower())

                assigned_to = users_bindings.get(issue['assignee']['id'] if issue['assignee'] else None, None)

                external_reference = None
                if options.get('keep_external_reference', False):
                    external_reference = ["github", issue['html_url']]

                us = UserStory.objects.create(
                    ref=issue['number'],
                    project=project,
                    owner=users_bindings.get(issue['user']['id'], self._user),
                    milestone=project.milestones.get(name=issue['milestone']['title']) if issue['milestone'] else None,
                    assigned_to=assigned_to,
                    status=project.us_statuses.get(slug=issue['state']),
                    kanban_order=issue['number'],
                    sprint_order=issue['number'],
                    backlog_order=issue['number'],
                    subject=issue['title'],
                    description=issue.get("body", "") or "",
                    tags=tags,
                    external_reference=external_reference,
                    modified_date=issue['updated_at'],
                    created_date=issue['created_at'],
                )

                assignees = issue.get('assignees', [])
                if len(assignees) > 1:
                    for assignee in assignees:
                        if assignee['id'] != issue.get('assignee', {}).get('id', None):
                            assignee_user = users_bindings.get(assignee['id'], None)
                            if assignee_user is not None:
                                us.add_watcher(assignee_user)

                UserStory.objects.filter(id=us.id).update(
                    ref=issue['number'],
                    modified_date=issue['updated_at'],
                    created_date=issue['created_at']
                )

                take_snapshot(us, comment="", user=None, delete=False)

            if len(issues) < 100:
                break

    def _import_issues_data(self, project, repo, options):
        users_bindings = options.get('users_bindings', {})

        page = 1
        while True:
            issues = self._client.get("/repos/{}/issues".format(repo['full_name']), {
                "state": "all",
                "sort": "created",
                "direction": "asc",
                "page": page,
                "per_page": 100
            })
            page += 1
            for issue in issues:
                tags = []
                for label in issue['labels']:
                    tags.append(label['name'].lower())

                assigned_to = users_bindings.get(issue['assignee']['id'] if issue['assignee'] else None, None)

                external_reference = None
                if options.get('keep_external_reference', False):
                    external_reference = ["github", issue['html_url']]

                taiga_issue = Issue.objects.create(
                    ref=issue['number'],
                    project=project,
                    owner=users_bindings.get(issue['user']['id'], self._user),
                    assigned_to=assigned_to,
                    status=project.issue_statuses.get(slug=issue['state']),
                    subject=issue['title'],
                    description=issue.get('body', "") or "",
                    tags=tags,
                    external_reference=external_reference,
                    modified_date=issue['updated_at'],
                    created_date=issue['created_at'],
                )

                assignees = issue.get('assignees', [])
                if len(assignees) > 1:
                    for assignee in assignees:
                        if assignee['id'] != issue.get('assignee', {}).get('id', None):
                            assignee_user = users_bindings.get(assignee['id'], None)
                            if assignee_user is not None:
                                taiga_issue.add_watcher(assignee_user)

                Issue.objects.filter(id=taiga_issue.id).update(
                    ref=issue['number'],
                    modified_date=issue['updated_at'],
                    created_date=issue['created_at']
                )

                take_snapshot(taiga_issue, comment="", user=None, delete=False)

            if len(issues) < 100:
                break

    def _import_comments(self, project, repo, options):
        users_bindings = options.get('users_bindings', {})

        page = 1
        while True:
            comments = self._client.get("/repos/{}/issues/comments".format(repo['full_name']), {
                "page": page,
                "per_page": 100
            })
            page += 1

            for comment in comments:
                issue_id = comment['issue_url'].split("/")[-1]
                if options.get('type', None) == "user_stories":
                    obj = UserStory.objects.get(project=project, ref=issue_id)
                elif options.get('type', None) == "issues":
                    obj = Issue.objects.get(project=project, ref=issue_id)

                snapshot = take_snapshot(
                    obj,
                    comment=comment['body'],
                    user=users_bindings.get(comment['user']['id'], User(full_name=comment['user'].get('name', None) or comment['user']['login'])),
                    delete=False
                )
                HistoryEntry.objects.filter(id=snapshot.id).update(created_at=comment['created_at'])

            if len(comments) < 100:
                break

    def _import_history(self, project, repo, options):
        cumulative_data = {}
        page = 1
        all_events = []
        while True:
            events = self._client.get("/repos/{}/issues/events".format(repo['full_name']), {
                "page": page,
                "per_page": 100
            })
            page += 1
            all_events = all_events + events

            if len(events) < 100:
                break

        for event in sorted(all_events, key=lambda x: x['id']):
            if options.get('type', None) == "user_stories":
                obj = UserStory.objects.get(project=project, ref=event['issue']['number'])
            elif options.get('type', None) == "issues":
                obj = Issue.objects.get(project=project, ref=event['issue']['number'])

            if event['issue']['number'] in cumulative_data:
                obj_cumulative_data = cumulative_data[event['issue']['number']]
            else:
                obj_cumulative_data = {
                    "tags": set(),
                    "assigned_to": None,
                    "assigned_to_github_id": None,
                    "assigned_to_name": None,
                    "milestone": None,
                }
                cumulative_data[event['issue']['number']] = obj_cumulative_data
            self._import_event(obj, event, options, obj_cumulative_data)

    def _import_event(self, obj, event, options, cumulative_data):
        typename = get_typename_for_model_class(type(obj))
        key = make_key_from_model_object(obj)
        event_data = self._transform_event_data(obj, event, options, cumulative_data)
        if event_data is None:
            return

        change_old = event_data['change_old']
        change_new = event_data['change_new']
        user = event_data['user']

        diff = make_diff_from_dicts(change_old, change_new)
        fdiff = FrozenDiff(key, diff, {})
        values = make_diff_values(typename, fdiff)
        values.update(event_data['update_values'])
        entry = HistoryEntry.objects.create(
            user=user,
            project_id=obj.project.id,
            key=key,
            type=HistoryType.change,
            snapshot=None,
            diff=fdiff.diff,
            values=values,
            comment="",
            comment_html="",
            is_hidden=False,
            is_snapshot=False,
        )
        HistoryEntry.objects.filter(id=entry.id).update(created_at=event['created_at'])
        return HistoryEntry.objects.get(id=entry.id)

    def _transform_event_data(self, obj, event, options, cumulative_data):
        users_bindings = options.get('users_bindings', {})

        ignored_events = ["committed", "cross-referenced", "head_ref_deleted",
                          "head_ref_restored", "locked", "unlocked", "merged",
                          "referenced", "mentioned", "subscribed",
                          "unsubscribed"]

        if event['event'] in ignored_events:
            return None

        user = {"pk": None, "name": event['actor'].get('name', event['actor']['login'])}
        taiga_user = users_bindings.get(event['actor']['id'], None) if event['actor'] else None
        if taiga_user:
            user = {"pk": taiga_user.id, "name": taiga_user.get_full_name()}

        result = {
            "change_old": {},
            "change_new": {},
            "user": user,
            "update_values": {},
        }

        if event['event'] == "renamed":
            result['change_old']["subject"] = event['rename']['from']
            result['change_new']["subject"] = event['rename']['to']
        elif event['event'] == "reopened":
            if isinstance(obj, Issue):
                result['change_old']["status"] = obj.project.issue_statuses.get(name='Closed').id
                result['change_new']["status"] = obj.project.issue_statuses.get(name='Open').id
            elif isinstance(obj, UserStory):
                result['change_old']["status"] = obj.project.us_statuses.get(name='Closed').id
                result['change_new']["status"] = obj.project.us_statuses.get(name='Open').id
        elif event['event'] == "closed":
            if isinstance(obj, Issue):
                result['change_old']["status"] = obj.project.issue_statuses.get(name='Open').id
                result['change_new']["status"] = obj.project.issue_statuses.get(name='Closed').id
            elif isinstance(obj, UserStory):
                result['change_old']["status"] = obj.project.us_statuses.get(name='Open').id
                result['change_new']["status"] = obj.project.us_statuses.get(name='Closed').id
        elif event['event'] == "assigned":
            AssignedEventHandler(result, cumulative_data, users_bindings).handle(event)
        elif event['event'] == "unassigned":
            UnassignedEventHandler(result, cumulative_data, users_bindings).handle(event)
        elif event['event'] == "demilestoned":
            if isinstance(obj, UserStory):
                try:
                    result['change_old']["milestone"] = obj.project.milestones.get(name=event['milestone']['title']).id
                except Milestone.DoesNotExist:
                    result['change_old']["milestone"] = 0
                    result['update_values'] = {"milestone": {"0": event['milestone']['title']}}
                result['change_new']["milestone"] = None
                cumulative_data['milestone'] = None
        elif event['event'] == "milestoned":
            if isinstance(obj, UserStory):
                result['update_values']["milestone"] = {}
                if cumulative_data['milestone'] is not None:
                    result['update_values']['milestone'][str(cumulative_data['milestone'])] = cumulative_data['milestone_name']
                result['change_old']["milestone"] = cumulative_data['milestone']
                try:
                    taiga_milestone = obj.project.milestones.get(name=event['milestone']['title'])
                    cumulative_data["milestone"] = taiga_milestone.id
                    cumulative_data['milestone_name'] = taiga_milestone.name
                except Milestone.DoesNotExist:
                    if cumulative_data['milestone'] == 0:
                        cumulative_data['milestone'] = -1
                    else:
                        cumulative_data['milestone'] = 0
                    cumulative_data['milestone_name'] = event['milestone']['title']
                result['change_new']["milestone"] = cumulative_data['milestone']
                result['update_values']['milestone'][str(cumulative_data['milestone'])] = cumulative_data['milestone_name']
        elif event['event'] == "labeled":
            result['change_old']["tags"] = list(cumulative_data['tags'])
            cumulative_data['tags'].add(event['label']['name'].lower())
            result['change_new']["tags"] = list(cumulative_data['tags'])
        elif event['event'] == "unlabeled":
            result['change_old']["tags"] = list(cumulative_data['tags'])
            if event['label']['name'].lower() in cumulative_data['tags']:
                cumulative_data['tags'].remove(event['label']['name'].lower())
            result['change_new']["tags"] = list(cumulative_data['tags'])

        return result

    @classmethod
    def get_auth_url(cls, client_id, callback_uri=None):
        if callback_uri is None:
            return "https://github.com/login/oauth/authorize?client_id={}&scope=user,repo".format(client_id)
        return "https://github.com/login/oauth/authorize?client_id={}&scope=user,repo&redirect_uri={}".format(client_id, callback_uri)

    @classmethod
    def get_access_token(cls, client_id, client_secret, code):
        try:
            result = requests.post("https://github.com/login/oauth/access_token", {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            })
        except Exception:
            raise FailedRequest()

        if result.status_code > 299:
            raise InvalidAuthResult()
        else:
            try:
                return dict(parse_qsl(result.content))[b'access_token'].decode('utf-8')
            except:
                raise InvalidAuthResult()


class AssignedEventHandler:
    def __init__(self, result, cumulative_data, users_bindings):
        self.result = result
        self.cumulative_data = cumulative_data
        self.users_bindings = users_bindings

    def handle(self, event):
        if self.cumulative_data['assigned_to_github_id'] is None:
            self.result['update_values']["users"] = {}
            self.generate_change_old(event)
            self.generate_update_values_from_cumulative_data(event)
            user = self.users_bindings.get(event['assignee']['id'], None)
            self.generate_change_new(event, user)
            self.update_cumulative_data(event, user)
            self.generate_update_values_from_cumulative_data(event)

    def generate_change_old(self, event):
        self.result['change_old']["assigned_to"] = self.cumulative_data['assigned_to']

    def generate_update_values_from_cumulative_data(self, event):
        if self.cumulative_data['assigned_to_name'] is not None:
            self.result['update_values']["users"][str(self.cumulative_data['assigned_to'])] = self.cumulative_data['assigned_to_name']

    def generate_change_new(self, event, user):
        if user is None:
            self.result['change_new']["assigned_to"] = 0
        else:
            self.result['change_new']["assigned_to"] = user.id

    def update_cumulative_data(self, event, user):
        self.cumulative_data['assigned_to_github_id'] = event['assignee']['id']
        if user is None:
            self.cumulative_data['assigned_to'] = 0
            self.cumulative_data['assigned_to_name'] = event['assignee']['login']
        else:
            self.cumulative_data['assigned_to'] = user.id
            self.cumulative_data['assigned_to_name'] = user.get_full_name()


class UnassignedEventHandler:
    def __init__(self, result, cumulative_data, users_bindings):
        self.result = result
        self.cumulative_data = cumulative_data
        self.users_bindings = users_bindings

    def handle(self, event):
        if self.cumulative_data['assigned_to_github_id'] == event['assignee']['id']:
            self.result['update_values']["users"] = {}

            self.generate_change_old(event)
            self.generate_update_values_from_cumulative_data(event)
            self.generate_change_new(event)
            self.update_cumulative_data(event)
            self.generate_update_values_from_cumulative_data(event)

    def generate_change_old(self, event):
        self.result['change_old']["assigned_to"] = self.cumulative_data['assigned_to']

    def generate_update_values_from_cumulative_data(self, event):
        if self.cumulative_data['assigned_to_name'] is not None:
            self.result['update_values']["users"][str(self.cumulative_data['assigned_to'])] = self.cumulative_data['assigned_to_name']

    def generate_change_new(self, event):
        self.result['change_new']["assigned_to"] = None

    def update_cumulative_data(self, event):
        self.cumulative_data['assigned_to_github_id'] = None
        self.cumulative_data['assigned_to'] = None
        self.cumulative_data['assigned_to_name'] = None
