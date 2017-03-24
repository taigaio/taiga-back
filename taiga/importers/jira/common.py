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

import requests
from urllib.parse import parse_qsl, quote_plus
from oauthlib.oauth1 import SIGNATURE_RSA

from requests_oauthlib import OAuth1
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from taiga.users.models import User
from taiga.projects.models import Points
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.issues.models import Issue
from taiga.projects.milestones.models import Milestone
from taiga.projects.epics.models import Epic
from taiga.projects.attachments.models import Attachment
from taiga.projects.history.services import take_snapshot
from taiga.projects.history.services import (make_diff_from_dicts,
                                             make_diff_values,
                                             make_key_from_model_object,
                                             get_typename_for_model_class,
                                             FrozenDiff)
from taiga.projects.custom_attributes.models import (UserStoryCustomAttribute,
                                                     TaskCustomAttribute,
                                                     IssueCustomAttribute,
                                                     EpicCustomAttribute)
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.choices import HistoryType
from taiga.mdrender.service import render as mdrender
from taiga.importers import exceptions
from taiga.front.templatetags.functions import resolve as resolve_front_url

EPIC_COLORS = {
    "ghx-label-0": "#ffffff",
    "ghx-label-1": "#815b3a",
    "ghx-label-2": "#f79232",
    "ghx-label-3": "#d39c3f",
    "ghx-label-4": "#3b7fc4",
    "ghx-label-5": "#4a6785",
    "ghx-label-6": "#8eb021",
    "ghx-label-7": "#ac707a",
    "ghx-label-8": "#654982",
    "ghx-label-9": "#f15c75",
}


def links_to_richtext(importer, issue, links):
    richtext = ""
    importing_project_key = issue['key'].split("-")[0]
    for link in links:
        if "inwardIssue" in link:
            (project_key, issue_key) = link['inwardIssue']['key'].split("-")
            action = link['type']['inward']
        elif "outwardIssue" in link:
            (project_key, issue_key) = link['outwardIssue']['key'].split("-")
            action = link['type']['outward']
        else:
            continue

        if importing_project_key == project_key:
            richtext += "  * This item {} #{}\n".format(action, issue_key)
        else:
            url = importer._client.server + "/projects/{}/issues/{}-{}".format(
                project_key,
                project_key,
                issue_key
            )
            richtext += "  * This item {} [{}-{}]({})\n".format(action, project_key, issue_key, url)

    for link in links:
        if "object" in link:
            richtext += "  * [{}]({})\n".format(
                link['object']['title'] or link['object']['url'],
                link['object']['url'],
            )

    return richtext


class JiraClient:
    def __init__(self, server, oauth):
        self.server = server
        self.api_url = server + "/rest/agile/1.0/{}"
        self.main_api_url = server + "/rest/api/2/{}"
        if oauth:
            self.oauth = OAuth1(
                oauth['consumer_key'],
                signature_method=SIGNATURE_RSA,
                rsa_key=oauth['key_cert'],
                resource_owner_key=oauth['access_token'],
                resource_owner_secret=oauth['access_token_secret']
            )
        else:
            self.oauth = None

    def get(self, uri_path, query_params=None):
        headers = {
            'Content-Type': "application/json"
        }
        if query_params is None:
            query_params = {}

        if uri_path[0] == '/':
            uri_path = uri_path[1:]
        url = self.main_api_url.format(uri_path)

        response = requests.get(url, params=query_params, headers=headers, auth=self.oauth)

        if response.status_code == 401:
            raise Exception("Unauthorized: %s at %s" % (response.text, url), response)
        if response.status_code != 200:
            raise Exception("Resource Unavailable: %s at %s" % (response.text, url), response)

        return response.json()

    def get_agile(self, uri_path, query_params=None):
        headers = {
            'Content-Type': "application/json"
        }
        if query_params is None:
            query_params = {}

        if uri_path[0] == '/':
            uri_path = uri_path[1:]
        url = self.api_url.format(uri_path)

        response = requests.get(url, params=query_params, headers=headers, auth=self.oauth)

        if response.status_code == 401:
            raise Exception("Unauthorized: %s at %s" % (response.text, url), response)
        if response.status_code != 200:
            raise Exception("Resource Unavailable: %s at %s" % (response.text, url), response)

        return response.json()

    def raw_get(self, absolute_uri, query_params=None):
        if query_params is None:
            query_params = {}

        response = requests.get(absolute_uri, params=query_params, auth=self.oauth)

        if response.status_code == 401:
            raise Exception("Unauthorized: %s at %s" % (response.text, absolute_uri), response)
        if response.status_code != 200:
            raise Exception("Resource Unavailable: %s at %s" % (response.text, absolute_uri), response)

        return response.content

    def get_issue_url(self, key):
        (project_key, issue_key) = key.split("-")
        return self.server + "/projects/{}/issues/{}".format(project_key, key)


class JiraImporterCommon:
    def __init__(self, user, server, oauth):
        self._user = user
        self._client = JiraClient(server=server, oauth=oauth)

    def resolve_user_bindings(self, options):
        def resolve_user(user_id):
            if isinstance(user_id, User):
                return user_id
            try:
                user = User.objects.get(id=user_id)
                return user
            except User.DoesNotExist:
                return None

        options['users_bindings'] = {k: resolve_user(v) for k,v in options['users_bindings'].items() if v is not None}

    def list_users(self):
        result = []
        projects = self._client.get('/project')
        users = self._client.get("/user/assignable/multiProjectSearch", {
            "username": "",
            "projectKeys": list(map(lambda x: x['key'], projects)),
            "maxResults": 1000,
        })
        for user in users:
            user_data = self._client.get("/user", {
                "key": user['key']
            })
            result.append({
                "id": user_data['key'],
                "full_name": user_data['displayName'],
                "email": user_data['emailAddress'],
                "avatar": user_data.get('avatarUrls', None) and user_data['avatarUrls'].get('48x48', None),
            })
        return result

    def _import_comments(self, obj, issue, options):
        users_bindings = options.get('users_bindings', {})
        offset = 0
        while True:
            comments = self._client.get("/issue/{}/comment".format(issue['key']), {"startAt": offset})
            for comment in comments['comments']:
                snapshot = take_snapshot(
                    obj,
                    comment=comment['body'],
                    user=users_bindings.get(
                        comment['author']['name'],
                        User(full_name=comment['author']['displayName'])
                    ),
                    delete=False
                )
                HistoryEntry.objects.filter(id=snapshot.id).update(created_at=comment['created'])

            offset += len(comments['comments'])
            if len(comments['comments']) <= comments['maxResults']:
                break

    def _create_custom_fields(self, project):
        custom_fields = []
        for model in [UserStoryCustomAttribute, TaskCustomAttribute, IssueCustomAttribute, EpicCustomAttribute]:
            model.objects.create(
                name="Due date",
                description="Due date",
                type="date",
                order=1,
                project=project
            )
            model.objects.create(
                name="Priority",
                description="Priority",
                type="text",
                order=1,
                project=project
            )
            model.objects.create(
                name="Resolution",
                description="Resolution",
                type="text",
                order=1,
                project=project
            )
            model.objects.create(
                name="Resolution date",
                description="Resolution date",
                type="date",
                order=1,
                project=project
            )
            model.objects.create(
                name="Environment",
                description="Environment",
                type="text",
                order=1,
                project=project
            )
            model.objects.create(
                name="Components",
                description="Components",
                type="text",
                order=1,
                project=project
            )
            model.objects.create(
                name="Affects Version/s",
                description="Affects Version/s",
                type="text",
                order=1,
                project=project
            )
            model.objects.create(
                name="Fix Version/s",
                description="Fix Version/s",
                type="text",
                order=1,
                project=project
            )
            model.objects.create(
                name="Links",
                description="Links",
                type="richtext",
                order=1,
                project=project
            )
        custom_fields.append({
            "history_name": "duedate",
            "jira_field_name": "duedate",
            "taiga_field_name": "Due date",
        })
        custom_fields.append({
            "history_name": "priority",
            "jira_field_name": "priority",
            "taiga_field_name": "Priority",
            "transform": lambda issue, obj: obj.get('name', None)
        })
        custom_fields.append({
            "history_name": "resolution",
            "jira_field_name": "resolution",
            "taiga_field_name": "Resolution",
            "transform": lambda issue, obj: obj.get('name', None)
        })
        custom_fields.append({
            "history_name": "Resolution date",
            "jira_field_name": "resolutiondate",
            "taiga_field_name": "Resolution date",
        })
        custom_fields.append({
            "history_name": "environment",
            "jira_field_name": "environment",
            "taiga_field_name": "Environment",
        })
        custom_fields.append({
            "history_name": "Component",
            "jira_field_name": "components",
            "taiga_field_name": "Components",
            "transform": lambda issue, obj: ", ".join([c.get('name', None) for c in obj])
        })
        custom_fields.append({
            "history_name": "Version",
            "jira_field_name": "versions",
            "taiga_field_name": "Affects Version/s",
            "transform": lambda issue, obj: ", ".join([c.get('name', None) for c in obj])
        })
        custom_fields.append({
            "history_name": "Fix Version",
            "jira_field_name": "fixVersions",
            "taiga_field_name": "Fix Version/s",
            "transform": lambda issue, obj: ", ".join([c.get('name', None) for c in obj])
        })
        custom_fields.append({
            "history_name": "Link",
            "jira_field_name": "issuelinks",
            "taiga_field_name": "Links",
            "transform": lambda issue, obj: links_to_richtext(self, issue, obj)
        })

        greenhopper_fields = {}
        for custom_field in self._client.get("/field"):
            if custom_field['custom']:
                if custom_field['schema']['custom'] == "com.pyxis.greenhopper.jira:gh-sprint":
                    greenhopper_fields["sprint"] = custom_field['id']
                elif custom_field['schema']['custom'] == "com.pyxis.greenhopper.jira:gh-epic-link":
                    greenhopper_fields["link"] = custom_field['id']
                elif custom_field['schema']['custom'] == "com.pyxis.greenhopper.jira:gh-epic-status":
                    greenhopper_fields["status"] = custom_field['id']
                elif custom_field['schema']['custom'] == "com.pyxis.greenhopper.jira:gh-epic-label":
                    greenhopper_fields["label"] = custom_field['id']
                elif custom_field['schema']['custom'] == "com.pyxis.greenhopper.jira:gh-epic-color":
                    greenhopper_fields["color"] = custom_field['id']
                elif custom_field['schema']['custom'] == "com.pyxis.greenhopper.jira:gh-lexo-rank":
                    greenhopper_fields["rank"] = custom_field['id']
                elif (
                    custom_field['name'] == "Story Points" and
                    custom_field['schema']['custom'] == 'com.atlassian.jira.plugin.system.customfieldtypes:float'
                ):
                    greenhopper_fields["points"] = custom_field['id']
                else:
                    multiline_types = [
                        "com.atlassian.jira.plugin.system.customfieldtypes:textarea"
                    ]
                    date_types = [
                        "com.atlassian.jira.plugin.system.customfieldtypes:datepicker"
                        "com.atlassian.jira.plugin.system.customfieldtypes:datetime"
                    ]
                    if custom_field['schema']['custom'] in multiline_types:
                        field_type = "multiline"
                    elif custom_field['schema']['custom'] in date_types:
                        field_type = "date"
                    else:
                        field_type = "text"

                    custom_field_data = {
                        "name": custom_field['name'][:64],
                        "description": custom_field['name'],
                        "type": field_type,
                        "order": 1,
                        "project": project
                    }

                    UserStoryCustomAttribute.objects.get_or_create(**custom_field_data)
                    TaskCustomAttribute.objects.get_or_create(**custom_field_data)
                    IssueCustomAttribute.objects.get_or_create(**custom_field_data)
                    EpicCustomAttribute.objects.get_or_create(**custom_field_data)

                    custom_fields.append({
                        "history_name": custom_field['name'],
                        "jira_field_name": custom_field['id'],
                        "taiga_field_name": custom_field['name'][:64],
                    })

        self.greenhopper_fields = greenhopper_fields
        self.custom_fields = custom_fields

    def _import_to_custom_fields(self, obj, issue, options):
        if isinstance(obj, Epic):
            custom_att_manager = obj.project.epiccustomattributes
        elif isinstance(obj, UserStory):
            custom_att_manager = obj.project.userstorycustomattributes
        elif isinstance(obj, Task):
            custom_att_manager = obj.project.taskcustomattributes
        elif isinstance(obj, Issue):
            custom_att_manager = obj.project.issuecustomattributes
        else:
            raise NotImplementedError("Not implemented custom attributes for this object ({})".format(obj))

        custom_attributes_values = {}
        for custom_field in self.custom_fields:
            data = issue['fields'].get(custom_field['jira_field_name'], None)
            if data and "transform" in custom_field:
                data = custom_field['transform'](issue, data)

            if data:
                taiga_field = custom_att_manager.get(name=custom_field['taiga_field_name'])
                custom_attributes_values[taiga_field.id] = data

        if custom_attributes_values != {}:
            obj.custom_attributes_values.attributes_values = custom_attributes_values
            obj.custom_attributes_values.save()

    def _import_attachments(self, obj, issue, options):
        users_bindings = options.get('users_bindings', {})

        for attachment in issue['fields']['attachment']:
            try:
                data = self._client.raw_get(attachment['content'])
                att = Attachment(
                    owner=users_bindings.get(attachment['author']['name'], self._user),
                    project=obj.project,
                    content_type=ContentType.objects.get_for_model(obj),
                    object_id=obj.id,
                    name=attachment['filename'],
                    size=attachment['size'],
                    created_date=attachment['created'],
                    is_deprecated=False,
                )
                att.attached_file.save(attachment['filename'], ContentFile(data), save=True)
            except Exception:
                print("ERROR getting attachment url {}".format(attachment['content']))


    def _import_changelog(self, project, obj, issue, options):
        obj.cummulative_attachments = []
        for history in sorted(issue['changelog']['histories'], key=lambda h: h['created']):
            self._import_history(project, obj, history, options)

    def _import_history(self, project, obj, history, options):
        key = make_key_from_model_object(obj)
        typename = get_typename_for_model_class(obj.__class__)
        history_data = self._transform_history_data(project, obj, history, options)
        if history_data is None:
            return

        change_old = history_data['change_old']
        change_new = history_data['change_new']
        hist_type = history_data['hist_type']
        comment = history_data['comment']
        user = history_data['user']

        diff = make_diff_from_dicts(change_old, change_new)
        fdiff = FrozenDiff(key, diff, {})

        values = make_diff_values(typename, fdiff)
        values.update(history_data['update_values'])

        entry = HistoryEntry.objects.create(
            user=user,
            project_id=obj.project.id,
            key=key,
            type=hist_type,
            snapshot=None,
            diff=fdiff.diff,
            values=values,
            comment=comment,
            comment_html=mdrender(obj.project, comment),
            is_hidden=False,
            is_snapshot=False,
        )
        HistoryEntry.objects.filter(id=entry.id).update(created_at=history['created'])
        return HistoryEntry.objects.get(id=entry.id)

    def _transform_history_data(self, project, obj, history, options):
        users_bindings = options.get('users_bindings', {})

        user = {"pk": None, "name": history.get('author', {}).get('displayName', None)}
        taiga_user = users_bindings.get(history.get('author', {}).get('key', None), None)
        if taiga_user:
            user = {"pk": taiga_user.id, "name": taiga_user.get_full_name()}

        result = {
            "change_old": {},
            "change_new": {},
            "update_values": {},
            "hist_type": HistoryType.change,
            "comment": "",
            "user": user
        }
        custom_fields_by_names = {f["history_name"]: f for f in self.custom_fields}
        has_data = False
        for history_item in history['items']:
            if history_item['field'] == "Attachment":
                result['change_old']["attachments"] = []
                for att in obj.cummulative_attachments:
                    result['change_old']["attachments"].append({
                        "id": 0,
                        "filename": att
                    })

                if history_item['from'] is not None:
                    try:
                        idx = obj.cummulative_attachments.index(history_item['fromString'])
                        obj.cummulative_attachments.pop(idx)
                    except ValueError:
                        print("ERROR: Removing attachment that doesn't exist in the history ({})".format(history_item['fromString']))
                if history_item['to'] is not None:
                    obj.cummulative_attachments.append(history_item['toString'])

                result['change_new']["attachments"] = []
                for att in obj.cummulative_attachments:
                    result['change_new']["attachments"].append({
                        "id": 0,
                        "filename": att
                    })
                has_data = True
            elif history_item['field'] == "description":
                result['change_old']["description"] = history_item['fromString']
                result['change_new']["description"] = history_item['toString']
                result['change_old']["description_html"] = mdrender(obj.project, history_item['fromString'] or "")
                result['change_new']["description_html"] = mdrender(obj.project, history_item['toString'] or "")
                has_data = True
            elif history_item['field'] == "Epic Link":
                pass
            elif history_item['field'] == "Workflow":
                pass
            elif history_item['field'] == "Link":
                pass
            elif history_item['field'] == "labels":
                result['change_old']["tags"] = history_item['fromString'].split()
                result['change_new']["tags"] = history_item['toString'].split()
                has_data = True
            elif history_item['field'] == "Rank":
                pass
            elif history_item['field'] == "RemoteIssueLink":
                pass
            elif history_item['field'] == "Sprint":
                old_milestone = None
                if history_item['fromString']:
                    try:
                        old_milestone = obj.project.milestones.get(name=history_item['fromString']).id
                    except Milestone.DoesNotExist:
                        old_milestone = -1

                new_milestone = None
                if history_item['toString']:
                    try:
                        new_milestone = obj.project.milestones.get(name=history_item['toString']).id
                    except Milestone.DoesNotExist:
                        new_milestone = -2

                result['change_old']["milestone"] = old_milestone
                result['change_new']["milestone"] = new_milestone

                if old_milestone == -1 or new_milestone == -2:
                    result['update_values']["milestone"] = {}

                if old_milestone == -1:
                    result['update_values']["milestone"]["-1"] = history_item['fromString']
                if new_milestone == -2:
                    result['update_values']["milestone"]["-2"] = history_item['toString']
                has_data = True
            elif history_item['field'] == "status":
                if isinstance(obj, Task):
                    try:
                        old_status = obj.project.task_statuses.get(name=history_item['fromString']).id
                    except Exception:
                        old_status = -1
                    try:
                        new_status = obj.project.task_statuses.get(name=history_item['toString']).id
                    except Exception:
                        new_status = -2
                elif isinstance(obj, UserStory):
                    try:
                        old_status = obj.project.us_statuses.get(name=history_item['fromString']).id
                    except Exception:
                        old_status = -1
                    try:
                        new_status = obj.project.us_statuses.get(name=history_item['toString']).id
                    except Exception:
                        new_status = -2
                elif isinstance(obj, Issue):
                    try:
                        old_status = obj.project.issue_statuses.get(name=history_item['fromString']).id
                    except Exception:
                        old_status = -1
                    try:
                        new_status = obj.project.us_statuses.get(name=history_item['toString']).id
                    except Exception:
                        new_status = -2
                elif isinstance(obj, Epic):
                    try:
                        old_status = obj.project.epic_statuses.get(name=history_item['fromString']).id
                    except Exception:
                        old_status = -1
                    try:
                        new_status = obj.project.epic_statuses.get(name=history_item['toString']).id
                    except Exception:
                        new_status = -2

                if old_status == -1 or new_status == -2:
                    result['update_values']["status"] = {}

                if old_status == -1:
                    result['update_values']["status"]["-1"] = history_item['fromString']
                if new_status == -2:
                    result['update_values']["status"]["-2"] = history_item['toString']

                result['change_old']["status"] = old_status
                result['change_new']["status"] = new_status
                has_data = True
            elif history_item['field'] == "Story Points":
                old_points = None
                if history_item['fromString']:
                    estimation = float(history_item['fromString'])
                    (old_points, _) = Points.objects.get_or_create(
                        project=project,
                        value=estimation,
                        defaults={
                            "name": str(estimation),
                            "order": estimation,
                        }
                    )
                    old_points = old_points.id
                new_points = None
                if history_item['toString']:
                    estimation = float(history_item['toString'])
                    (new_points, _) = Points.objects.get_or_create(
                        project=project,
                        value=estimation,
                        defaults={
                            "name": str(estimation),
                            "order": estimation,
                        }
                    )
                    new_points = new_points.id
                result['change_old']["points"] = {project.roles.get(slug="main").id: old_points}
                result['change_new']["points"] = {project.roles.get(slug="main").id: new_points}
                has_data = True
            elif history_item['field'] == "summary":
                result['change_old']["subject"] = history_item['fromString']
                result['change_new']["subject"] = history_item['toString']
                has_data = True
            elif history_item['field'] == "Epic Color":
                if isinstance(obj, Epic):
                    result['change_old']["color"] = EPIC_COLORS.get(history_item['fromString'], None)
                    result['change_new']["color"] = EPIC_COLORS.get(history_item['toString'], None)
                    Epic.objects.filter(id=obj.id).update(
                        color=EPIC_COLORS.get(history_item['toString'], "#999999")
                    )
                    has_data = True
            elif history_item['field'] == "assignee":
                old_assigned_to = None
                if history_item['from'] is not None:
                    old_assigned_to = users_bindings.get(history_item['from'], -1)
                    if old_assigned_to != -1:
                        old_assigned_to = old_assigned_to.id

                new_assigned_to = None
                if history_item['to'] is not None:
                    new_assigned_to = users_bindings.get(history_item['to'], -2)
                    if new_assigned_to != -2:
                        new_assigned_to = new_assigned_to.id

                result['change_old']["assigned_to"] = old_assigned_to
                result['change_new']["assigned_to"] = new_assigned_to

                if old_assigned_to == -1 or new_assigned_to == -2:
                    result['update_values']["users"] = {}

                if old_assigned_to == -1:
                    result['update_values']["users"]["-1"] = history_item['fromString']
                if new_assigned_to == -2:
                    result['update_values']["users"]["-2"] = history_item['toString']
                has_data = True
            elif history_item['field'] in custom_fields_by_names:
                custom_field = custom_fields_by_names[history_item['field']]
                if isinstance(obj, Task):
                    field_obj = obj.project.taskcustomattributes.get(name=custom_field['taiga_field_name'])
                elif isinstance(obj, UserStory):
                    field_obj = obj.project.userstorycustomattributes.get(name=custom_field['taiga_field_name'])
                elif isinstance(obj, Issue):
                    field_obj = obj.project.issuecustomattributes.get(name=custom_field['taiga_field_name'])
                elif isinstance(obj, Epic):
                    field_obj = obj.project.epiccustomattributes.get(name=custom_field['taiga_field_name'])

                result['change_old']["custom_attributes"] = [{
                    "name": custom_field['taiga_field_name'],
                    "value": history_item['fromString'],
                    "id": field_obj.id
                }]
                result['change_new']["custom_attributes"] = [{
                    "name": custom_field['taiga_field_name'],
                    "value": history_item['toString'],
                    "id": field_obj.id
                }]
                has_data = True

        if not has_data:
            return None

        return result

    def _cleanup(self, project, options):
        for epic_custom_field in project.epiccustomattributes.all():
            if project.epics.filter(custom_attributes_values__attributes_values__has_key=str(epic_custom_field.id)).count() == 0:
                epic_custom_field.delete()
        for us_custom_field in project.userstorycustomattributes.all():
            if project.user_stories.filter(custom_attributes_values__attributes_values__has_key=str(us_custom_field.id)).count() == 0:
                us_custom_field.delete()
        for task_custom_field in project.taskcustomattributes.all():
            if project.tasks.filter(custom_attributes_values__attributes_values__has_key=str(task_custom_field.id)).count() == 0:
                task_custom_field.delete()
        for issue_custom_field in project.issuecustomattributes.all():
            if project.issues.filter(custom_attributes_values__attributes_values__has_key=str(issue_custom_field.id)).count() == 0:
                issue_custom_field.delete()

    @classmethod
    def get_auth_url(cls, server, consumer_key, key_cert_data, verify=None):
        if verify is None:
            verify = server.startswith('https')

        callback_uri = resolve_front_url("project-import-jira", quote_plus(server))
        oauth = OAuth1(consumer_key, signature_method=SIGNATURE_RSA, rsa_key=key_cert_data, callback_uri=callback_uri)

        r = requests.post(
            server + '/plugins/servlet/oauth/request-token', verify=verify, auth=oauth)
        if r.status_code != 200:
            raise exceptions.InvalidServiceConfiguration()
        request = dict(parse_qsl(r.text))
        request_token = request['oauth_token']
        request_token_secret = request['oauth_token_secret']

        return (
            request_token,
            request_token_secret,
            '{}/plugins/servlet/oauth/authorize?oauth_token={}'.format(server, request_token)
        )

    @classmethod
    def get_access_token(cls, server, consumer_key, key_cert_data, request_token, request_token_secret, request_verifier, verify=False):
        callback_uri = resolve_front_url("project-import-jira", quote_plus(server))
        oauth = OAuth1(
            consumer_key,
            signature_method=SIGNATURE_RSA,
            callback_uri=callback_uri,
            rsa_key=key_cert_data,
            resource_owner_key=request_token,
            resource_owner_secret=request_token_secret,
            verifier=request_verifier,
        )
        r = requests.post(server + '/plugins/servlet/oauth/access-token', verify=verify, auth=oauth)
        access = dict(parse_qsl(r.text))

        return {
            'access_token': access['oauth_token'],
            'access_token_secret': access['oauth_token_secret'],
            'consumer_key': consumer_key,
            'key_cert': key_cert_data
        }
