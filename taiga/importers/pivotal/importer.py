# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
import requests

from taiga.users.models import User
from taiga.projects.references.models import recalc_reference_counter
from taiga.projects.models import Project, ProjectTemplate, Membership, Points
from taiga.projects.userstories.models import UserStory, RolePoints
from taiga.projects.tasks.models import Task
from taiga.projects.milestones.models import Milestone
from taiga.projects.epics.models import Epic, RelatedUserStory
from taiga.projects.attachments.models import Attachment
from taiga.projects.history.services import take_snapshot
from taiga.projects.history.services import (make_diff_from_dicts,
                                             make_diff_values,
                                             make_key_from_model_object,
                                             get_typename_for_model_class,
                                             FrozenDiff)
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.choices import HistoryType
from taiga.projects.custom_attributes.models import UserStoryCustomAttribute
from taiga.mdrender.service import render as mdrender
from taiga.timeline.rebuilder import rebuild_timeline
from taiga.timeline.models import Timeline


class PivotalClient:
    def __init__(self, token):
        self.api_url = "https://www.pivotaltracker.com/services/v5/{}"
        self.token = token
        self.me = self.get('/me')

    def get(self, uri_path, query_params=None):
        headers = {
            'X-TrackerToken': self.token
        }
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

    def get_attachment(self, attachment_id):
        headers = {
            'X-TrackerToken': self.token
        }
        url = "https://www.pivotaltracker.com/file_attachments/{}/download".format(attachment_id)
        response = requests.get(url, headers=headers)
        return response.content


class PivotalImporter:
    def __init__(self, user, token):
        self._user = user
        self._client = PivotalClient(token=token)

    def list_projects(self):
        return self._client.me['projects']

    def list_users(self, project_id):
        return self._client.get("/projects/{}/memberships".format(project_id))

    def import_project(self, project_id, options={"template": "scrum", "users_bindings": {}, "keep_external_reference": False}):
        (project, project_data) = self._import_project_data(project_id, options)
        self._import_epics_data(project_data, project, options)
        self._import_user_stories_data(project_data, project, options)
        Timeline.objects.filter(project=project).delete()
        rebuild_timeline(None, None, project.id)
        recalc_reference_counter(project)

    def _import_project_data(self, project_id, options):
        project_data = self._client.get(
            "/projects/{}".format(project_id),
            {
                "fields": ",".join([
                    "point_scale",
                    "name",
                    "description",
                    "labels(name)",
                ])
            }
        )
        project_data['iterations'] = self._client.get(
            "/projects/{}/iterations".format(project_id),
            {
                "fields": ",".join([
                    "number",
                    "start",
                    "finish",
                    "stories",
                ])
            }
        )
        project_data['epics'] = self._client.get(
            "/projects/{}/epics".format(project_data['id']),
            {
                "fields": ",".join([
                    "name",
                    "label",
                    "description",
                    "comments(text,file_attachments,google_attachments,person,created_at)",
                    "follower_ids",
                    "created_at",
                    "updated_at",
                    "url",
                ])
            }
        )

        project_template = ProjectTemplate.objects.get(slug=options['template'])
        project_template.is_epics_activated = True
        project_template.us_statuses = []
        project_template.points = [{
            "value": None,
            "name": "?",
            "order": 1,
        }]

        counter = 2
        for points in project_data['point_scale'].split(","):
            project_template.points.append({
                "value": int(points),
                "name": points,
                "order": counter
            })
            counter += 1

        project_template.us_statuses.append({
            "name": "Unscheduled",
            "slug": "unscheduled",
            "is_closed": True,
            "is_archived": False,
            "color": "#999999",
            "wip_limit": None,
            "order": 1,
        })
        project_template.us_statuses.append({
            "name": "Unstarted",
            "slug": "unstarted",
            "is_closed": False,
            "is_archived": False,
            "color": "#999999",
            "wip_limit": None,
            "order": 2,
        })
        project_template.us_statuses.append({
            "name": "Planned",
            "slug": "planned",
            "is_closed": False,
            "is_archived": False,
            "color": "#999999",
            "wip_limit": None,
            "order": 3,
        })
        project_template.us_statuses.append({
            "name": "Started",
            "slug": "started",
            "is_closed": False,
            "is_archived": False,
            "color": "#999999",
            "wip_limit": None,
            "order": 4,
        })
        project_template.us_statuses.append({
            "name": "Finished",
            "slug": "finished",
            "is_closed": False,
            "is_archived": False,
            "color": "#999999",
            "wip_limit": None,
            "order": 5,
        })
        project_template.us_statuses.append({
            "name": "Delivered",
            "slug": "delivered",
            "is_closed": True,
            "is_archived": False,
            "color": "#999999",
            "wip_limit": None,
            "order": 6,
        })
        project_template.us_statuses.append({
            "name": "Rejected",
            "slug": "rejected",
            "is_closed": True,
            "is_archived": True,
            "color": "#999999",
            "wip_limit": None,
            "order": 7,
        })
        project_template.us_statuses.append({
            "name": "Accepted",
            "slug": "accepted",
            "is_closed": True,
            "is_archived": True,
            "color": "#999999",
            "wip_limit": None,
            "order": 8,
        })
        project_template.default_options["us_status"] = "Unscheduled"

        project_template.task_statuses = []
        project_template.task_statuses.append({
            "name": "Incomplete",
            "slug": "incomplete",
            "is_closed": False,
            "color": "#ff8a84",
            "order": 1,
        })
        project_template.task_statuses.append({
            "name": "Complete",
            "slug": "complete",
            "is_closed": True,
            "color": "#669900",
            "order": 2,
        })
        project_template.default_options["task_status"] = "Incomplete"

        main_permissions = project_template.roles[0]['permissions']
        project_template.roles = [{
            "name": "Main",
            "slug": "main",
            "computable": True,
            "permissions": main_permissions,
            "order": 70,
        }]

        tags_colors = []
        for label in project_data['labels']:
            name = label['name'].lower()
            tags_colors.append([name, None])

        project = Project.objects.create(
            name=project_data['name'],
            description=project_data.get('description', ''),
            owner=self._user,
            tags_colors=tags_colors,
            creation_template=project_template
        )

        UserStoryCustomAttribute.objects.create(
            name="Due date",
            description="Due date",
            type="date",
            order=1,
            project=project
        )
        UserStoryCustomAttribute.objects.create(
            name="Type",
            description="Story type",
            type="text",
            order=2,
            project=project
        )
        for user in options.get('users_bindings', {}).values():
            if user != self._user:
                Membership.objects.get_or_create(
                    user=user,
                    project=project,
                    role=project.get_roles().get(slug="main"),
                    is_admin=False,
                )

        for iteration in project_data['iterations']:
            milestone = Milestone.objects.create(
                name="Sprint {}".format(iteration['number']),
                slug="sprint-{}".format(iteration['number']),
                owner=self._user,
                project=project,
                estimated_start=iteration['start'][:10],
                estimated_finish=iteration['finish'][:10],
            )
            Milestone.objects.filter(id=milestone.id).update(
                created_date=iteration['start'],
                modified_date=iteration['start'],
            )
        return (project, project_data)

    def _import_user_stories_data(self, project_data, project, options):
        users_bindings = options.get('users_bindings', {})
        epics = {e['label']['id']: e for e in project_data['epics']}
        due_date_field = project.userstorycustomattributes.get(name="Due date")
        story_type_field = project.userstorycustomattributes.get(name="Type")
        story_milestone_binding = {}
        for iteration in project_data['iterations']:
            for story in iteration['stories']:
                story_milestone_binding[story['id']] = Milestone.objects.get(
                    project=project,
                    slug="sprint-{}".format(iteration['number'])
                )

        counter = 0
        offset = 0
        while True:
            stories = self._client.get("/projects/{}/stories".format(project_data['id']), {
                "envelope": "true",
                "limit": 300,
                "offset": offset,
                "fields": ",".join([
                    "name",
                    "description",
                    "estimate",
                    "story_type",
                    "current_state",
                    "deadline",
                    "requested_by_id",
                    "owner_ids",
                    "labels(id,name)",
                    "comments(text,file_attachments,google_attachments,person,created_at)",
                    "tasks(id,description,position,complete,created_at,updated_at)",
                    "follower_ids",
                    "created_at",
                    "updated_at",
                    "url",
                ])})
            offset += 300
            for story in stories['data']:
                tags = []
                for label in story['labels']:
                    tags.append(label['name'])

                assigned_to = None
                if len(story['owner_ids']) > 0:
                    assigned_to = users_bindings.get(story['owner_ids'][0], None)

                owner = users_bindings.get(story['requested_by_id'], self._user)

                external_reference = None
                if options.get('keep_external_reference', False):
                    external_reference = ["pivotal", story['url']]

                us = UserStory.objects.create(
                    project=project,
                    owner=owner,
                    assigned_to=assigned_to,
                    status=project.us_statuses.get(slug=story['current_state']),
                    kanban_order=counter,
                    sprint_order=counter,
                    backlog_order=counter,
                    subject=story['name'],
                    description=story.get('description', ''),
                    tags=tags,
                    external_reference=external_reference,
                    milestone=story_milestone_binding.get(story['id'], None)
                )

                points = Points.objects.get(project=project, value=story.get('estimate', None))
                RolePoints.objects.filter(user_story=us, role__slug="main").update(points_id=points.id)

                if len(story['owner_ids']) > 1:
                    watchers = list(set(story['owner_ids'][1:] + story['follower_ids']))
                else:
                    watchers = story['follower_ids']

                for watcher in watchers:
                    watcher_user = users_bindings.get(watcher, None)
                    if watcher_user:
                        us.add_watcher(watcher_user)

                if story.get('deadline', None):
                    us.custom_attributes_values.attributes_values = {due_date_field.id: story['deadline']}
                    us.custom_attributes_values.save()
                if story.get('story_type', None):
                    us.custom_attributes_values.attributes_values = {story_type_field.id: story['story_type']}
                    us.custom_attributes_values.save()

                UserStory.objects.filter(id=us.id).update(
                    ref=story['id'],
                    modified_date=story['updated_at'],
                    created_date=story['created_at']
                )
                take_snapshot(us, comment="", user=None, delete=False)

                for label in story['labels']:
                    if epics.get(label['id'], None):
                        RelatedUserStory.objects.create(
                            epic=Epic.objects.get(project=project, ref=epics.get(label['id'])['id']),
                            user_story=us,
                            order=us.backlog_order
                        )
                self._import_tasks(project_data, us, story)
                self._import_user_story_activity(project_data, us, story, options)
                self._import_comments(project_data, us, story, options)
                counter += 1

            if len(stories['data']) < 300:
                break

    def _import_epics_data(self, project_data, project, options):
        users_bindings = options.get('users_bindings', {})
        counter = 0

        for epic in project_data['epics']:
            external_reference = None
            if options.get('keep_external_reference', False):
                external_reference = ["pivotal", epic['url']]

            taiga_epic = Epic.objects.create(
                project=project,
                owner=self._user,
                status=project.epic_statuses.get(slug="new"),
                epics_order=counter,
                subject=epic['name'],
                description=epic.get('description', ''),
                tags=[],
                external_reference=external_reference
            )

            Epic.objects.filter(id=taiga_epic.id).update(
                ref=epic['id'],
                modified_date=epic['updated_at'],
                created_date=epic['created_at']
            )

            for watcher in epic['follower_ids']:
                watcher_user = users_bindings.get(watcher, None)
                if watcher_user:
                    taiga_epic.add_watcher(watcher_user)

            take_snapshot(taiga_epic, comment="", user=None, delete=False)
            self._import_comments(project_data, taiga_epic, epic, options)
            self._import_epic_activity(project_data, taiga_epic, epic, options)
            counter += 1

    def _import_tasks(self, project_data, us, story):
        for task in story['tasks']:
            taiga_task = Task.objects.create(
                subject=task['description'],
                status=us.project.task_statuses.get(slug="complete" if task['complete'] else "incomplete"),
                project=us.project,
                us_order=task['position'],
                taskboard_order=task['position'],
                user_story=us
            )

            Task.objects.filter(id=taiga_task.id).update(
                ref=task['id'],
                modified_date=task['updated_at'],
                created_date=task['created_at']
            )
            take_snapshot(taiga_task, comment="", user=None, delete=False)

    def _import_attachment(self, obj, attachment_id, attachment_name, created_at, person_id, options):
        users_bindings = options.get('users_bindings', {})

        data = self._client.get_attachment(attachment_id)
        att = Attachment(
            owner=users_bindings.get(person_id, self._user),
            project=obj.project,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
            name=attachment_name,
            size=len(data),
            created_date=created_at,
            is_deprecated=False,
        )
        att.attached_file.save(attachment_name, ContentFile(data), save=True)

    def _import_comments(self, project_data, obj, story, options):
        users_bindings = options.get('users_bindings', {})

        for comment in story['comments']:
            if 'text' in comment:
                snapshot = take_snapshot(
                    obj,
                    comment=comment['text'],
                    user=users_bindings.get(comment['person']['id'], User(full_name=comment['person']['name'])),
                    delete=False
                )
                HistoryEntry.objects.filter(id=snapshot.id).update(created_at=comment['created_at'])
            for attachment in comment['file_attachments']:
                self._import_attachment(
                    obj,
                    attachment['id'],
                    attachment['filename'],
                    comment['created_at'],
                    comment['person']['id'],
                    options
                )

    def _import_user_story_activity(self, project_data, us, story, options):
        offset = 0
        while True:
            activities = self._client.get(
                "/projects/{}/stories/{}/activity".format(
                    project_data['id'],
                    story['id'],
                ),
                {"envelope": "true", "limit": 300, "offset": offset}
            )
            offset += 300
            for activity in activities['data']:
                self._import_activity(us, activity, options)

            if len(activities['data']) < 300:
                break

    def _import_epic_activity(self, project_data, taiga_epic, epic, options):
        offset = 0
        while True:
            activities = self._client.get(
                "/projects/{}/epics/{}/activity".format(
                    project_data['id'],
                    epic['id'],
                ),
                {"envelope": "true", "limit": 300, "offset": offset}
            )
            offset += 300
            for activity in activities['data']:
                self._import_activity(taiga_epic, activity, options)

            if len(activities['data']) < 300:
                break

    def _import_activity(self, obj, activity, options):
        activity_data = self._transform_activity_data(obj, activity, options)
        if activity_data is None:
            return

        change_old = activity_data['change_old']
        change_new = activity_data['change_new']
        hist_type = activity_data['hist_type']
        comment = activity_data['comment']
        user = activity_data['user']

        key = make_key_from_model_object(activity_data['obj'])
        typename = get_typename_for_model_class(type(activity_data['obj']))

        diff = make_diff_from_dicts(change_old, change_new)
        fdiff = FrozenDiff(key, diff, {})

        entry = HistoryEntry.objects.create(
            user=user,
            project_id=obj.project.id,
            key=key,
            type=hist_type,
            snapshot=None,
            diff=fdiff.diff,
            values=make_diff_values(typename, fdiff),
            comment=comment,
            comment_html=mdrender(obj.project, comment),
            is_hidden=False,
            is_snapshot=False,
        )
        HistoryEntry.objects.filter(id=entry.id).update(created_at=activity['occurred_at'])
        return HistoryEntry.objects.get(id=entry.id)

    def _transform_activity_data(self, obj, activity, options):
        users_bindings = options.get('users_bindings', {})
        due_date_field = obj.project.userstorycustomattributes.get(name="Due date")
        story_type_field = obj.project.userstorycustomattributes.get(name="Type")

        user = {"pk": None, "name": activity.get('performed_by', {}).get('name', None)}
        taiga_user = users_bindings.get(activity.get('performed_by', {}).get('id', None), None)
        if taiga_user:
            user = {"pk": taiga_user.id, "name": taiga_user.get_full_name()}

        result = {
            "change_old": {},
            "change_new": {},
            "hist_type": HistoryType.change,
            "comment": "",
            "user": user,
            "obj": obj
        }

        if activity['kind'] == "story_create_activity":
            UserStory.objects.filter(id=obj.id, created_date__gt=activity['occurred_at']).update(
                created_date=activity['occurred_at'],
                owner=users_bindings.get(activity["performed_by"]["id"], self._user)
            )
            return None
        elif activity['kind'] == "epic_create_activity":
            Epic.objects.filter(id=obj.id, created_date__gt=activity['occurred_at']).update(
                created_date=activity['occurred_at'],
                owner=users_bindings.get(activity["performed_by"]["id"], self._user)
            )
            return None
        elif activity['kind'] in ["story_update_activity", "epic_update_activity"]:
            for change in activity['changes']:
                if change['change_type'] != "update" or change['kind'] not in ["story", "epic"]:
                    continue

                if 'description' in change['new_values']:
                    result['change_old']["description"] = str(change['original_values']['description'])
                    result['change_new']["description"] = str(change['new_values']['description'])
                    result['change_old']["description_html"] = mdrender(obj.project, str(change['original_values']['description']))
                    result['change_new']["description_html"] = mdrender(obj.project, str(change['new_values']['description']))

                if 'estimate' in change['new_values']:
                    old_points = None
                    if change['original_values']['estimate']:
                        estimation = change['original_values']['estimate']
                        (old_points, _) = Points.objects.get_or_create(
                            project=obj.project,
                            value=estimation,
                            defaults={
                                "name": str(estimation),
                                "order": estimation,
                            }
                        )
                        old_points = old_points.id
                    new_points = None
                    if change['new_values']['estimate']:
                        estimation = change['new_values']['estimate']
                        (new_points, _) = Points.objects.get_or_create(
                            project=obj.project,
                            value=estimation,
                            defaults={
                                "name": str(estimation),
                                "order": estimation,
                            }
                        )
                        new_points = new_points.id
                    result['change_old']["points"] = {obj.project.roles.get(slug="main").id: old_points}
                    result['change_new']["points"] = {obj.project.roles.get(slug="main").id: new_points}

                if 'name' in change['new_values']:
                    result['change_old']["subject"] = change['original_values']['name']
                    result['change_new']["subject"] = change['new_values']['name']

                if 'labels' in change['new_values']:
                    result['change_old']["tags"] = [l.lower() for l in change['original_values']['labels']]
                    result['change_new']["tags"] = [l.lower() for l in change['new_values']['labels']]

                if 'current_state' in change['new_values']:
                    result['change_old']["status"] = obj.project.us_statuses.get(slug=change['original_values']['current_state']).id
                    result['change_new']["status"] = obj.project.us_statuses.get(slug=change['new_values']['current_state']).id

                if 'story_type' in change['new_values']:
                    if "custom_attributes" not in result['change_old']:
                        result['change_old']["custom_attributes"] = []
                    if "custom_attributes" not in result['change_new']:
                        result['change_new']["custom_attributes"] = []

                    result['change_old']["custom_attributes"].append({
                        "name": "Type",
                        "value": change['original_values']['story_type'],
                        "id": story_type_field.id
                    })
                    result['change_new']["custom_attributes"].append({
                        "name": "Type",
                        "value": change['new_values']['story_type'],
                        "id": story_type_field.id
                    })

                if 'deadline' in change['new_values']:
                    if "custom_attributes" not in result['change_old']:
                        result['change_old']["custom_attributes"] = []
                    if "custom_attributes" not in result['change_new']:
                        result['change_new']["custom_attributes"] = []

                    result['change_old']["custom_attributes"].append({
                        "name": "Due date",
                        "value": change['original_values']['deadline'],
                        "id": due_date_field.id
                    })
                    result['change_new']["custom_attributes"].append({
                        "name": "Due date",
                        "value": change['new_values']['deadline'],
                        "id": due_date_field.id
                    })

                # TODO: Process owners_ids

        elif activity['kind'] == "task_create_activity":
            return None
        elif activity['kind'] == "task_update_activity":
            for change in activity['changes']:
                if change['change_type'] != "update" or change['kind'] != "task":
                    continue

                try:
                    task = Task.objects.get(project=obj.project, ref=change['id'])
                    if 'description' in change['new_values']:
                        result['change_old']["subject"] = change['original_values']['description']
                        result['change_new']["subject"] = change['new_values']['description']
                        result['obj'] = task
                    if 'complete' in change['new_values']:
                        result['change_old']["status"] = obj.project.task_statuses.get(slug="complete" if change['original_values']['complete'] else "incomplete").id
                        result['change_new']["status"] = obj.project.task_statuses.get(slug="complete" if change['new_values']['complete'] else "incomplete").id
                        result['obj'] = task
                except Task.DoesNotExist:
                    return None

        elif activity['kind'] == "comment_create_activity":
            return None
        elif activity['kind'] == "comment_update_activity":
            return None
        elif activity['kind'] == "story_move_activity":
            return None
        return result
