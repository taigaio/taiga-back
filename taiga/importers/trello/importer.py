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

from django.utils.translation import ugettext as _

from requests_oauthlib import OAuth1Session, OAuth1
from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
import requests
import webcolors

from django.template.defaultfilters import slugify
from taiga.base import exceptions as exc
from taiga.projects.services import projects as projects_service
from taiga.projects.models import Project, ProjectTemplate
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.attachments.models import Attachment
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
from taiga.front.templatetags.functions import resolve as resolve_front_url
from taiga.importers import services as import_service

from taiga.base import exceptions


class TrelloClient:
    def __init__(self, api_key, api_secret, token):
        self.api_key = api_key
        self.api_secret = api_secret
        self.token = token
        if self.token:
            self.oauth = OAuth1(
                client_key=self.api_key,
                client_secret=self.api_secret,
                resource_owner_key=self.token
            )
        else:
            self.oauth = None

    def get(self, uri_path, query_params=None):
        headers = {'Accept': 'application/json'}
        if query_params is None:
            query_params = {}

        if uri_path[0] == '/':
            uri_path = uri_path[1:]
        url = 'https://api.trello.com/1/%s' % uri_path

        response = requests.get(url, params=query_params, headers=headers, auth=self.oauth)

        if response.status_code == 400:
            raise exc.WrongArguments(_("Invalid Request: %s at %s") % (response.text, url))
        if response.status_code == 401:
            raise exc.AuthenticationFailed(_("Unauthorized: %s at %s") % (response.text, url))
        if response.status_code == 403:
            raise exc.PermissionDenied(_("Unauthorized: %s at %s") % (response.text, url))
        if response.status_code == 404:
            raise exc.NotFound(_("Resource Unavailable: %s at %s") % (response.text, url))
        if response.status_code != 200:
            raise exc.WrongArguments(_("Resource Unavailable: %s at %s") % (response.text, url))

        return response.json()


class TrelloImporter:
    def __init__(self, user, token):
        self._user = user
        self._cached_orgs = {}
        self._client = TrelloClient(
            api_key=settings.IMPORTERS.get('trello', {}).get('api_key', None),
            api_secret=settings.IMPORTERS.get('trello', {}).get('secret_key', None),
            token=token,
        )

    def list_projects(self):
        projects_data = self._client.get("/members/me/boards", {
            "fields": "id,name,desc,prefs,idOrganization",
            "organization": "true",
            "organization_fields": "prefs",
        })
        projects = []
        for project in projects_data:
            is_private = False
            if project['prefs']['permissionLevel'] == "private":
                is_private = True

            if project['prefs']['permissionLevel'] == "org":
                if 'organization' not in project:
                    is_private = True
                elif project['organization']['prefs']['permissionLevel'] == "private":
                    is_private = True

            projects.append({
                "id": project['id'],
                "name": project['name'],
                "description": project['desc'],
                "is_private": is_private,
            })
        return projects

    def list_users(self, project_id):
        members = []
        for member in self._client.get("/board/{}/members/all".format(project_id), {"fields": "id"}):
            user = self._client.get("/member/{}".format(member['id']), {"fields": "id,fullName,email,avatarSource,avatarHash,gravatarHash"})
            avatar = None
            try:
                if user['avatarSource'] == "gravatar" and user['gravatarHash']:
                    avatar = 'https://www.gravatar.com/avatar/' + user['gravatarHash'] + '.jpg?s=50'
                elif user['avatarHash'] is not None:
                    avatar = 'https://trello-avatars.s3.amazonaws.com/' + user['avatarHash'] + '/50.png'
            except:
                # NOTE: Sometimes this piece of code return this exception:
                #
                # File "/home/taiga/taiga-back/taiga/importers/trello/importer.py" in list_users
                #  135.   avatar = 'https://trello-avatars.s3.amazonaws.com/' + user['avatarHash'] + '/50.png'
                #
                # Exception Type: TypeError at /api/v1/importers/trello/list_users
                # Exception Value: Can't convert 'NoneType' object to str implicitly
                pass

            members.append({
                "id": user['id'],
                "full_name": user['fullName'],
                "email": user['email'],
                "avatar": avatar
            })
        return members

    def import_project(self, project_id, options):
        data = self._client.get(
            "/board/{}".format(project_id),
            {
                "fields": "name,desc",
                "cards": "all",
                "card_fields": "closed,labels,idList,desc,due,name,pos,dateLastActivity,idChecklists,idMembers,url",
                "card_attachments": "true",
                "labels": "all",
                "labels_limit": "1000",
                "lists": "all",
                "list_fields": "closed,name,pos",
                "members": "none",
                "checklists": "all",
                "checklist_fields": "name",
                "organization": "true",
                "organization_fields": "logoHash",
            }
        )

        project = self._import_project_data(data, options)
        self._import_user_stories_data(data, project, options)
        self._cleanup(project, options)
        Timeline.objects.filter(project=project).delete()
        rebuild_timeline(None, None, project.id)
        return project

    def _import_project_data(self, data, options):
        board = data
        labels = board['labels']
        statuses = board['lists']
        project_template = ProjectTemplate.objects.get(slug=options.get('template', "kanban"))
        project_template.us_statuses = []
        counter = 0
        for us_status in statuses:
            if counter == 0:
                project_template.default_options["us_status"] = us_status['name']

            counter += 1
            if us_status['name'] not in [s['name'] for s in project_template.us_statuses]:
                project_template.us_statuses.append({
                    "name": us_status['name'],
                    "slug": slugify(us_status['name']),
                    "is_closed": False,
                    "is_archived": True if us_status['closed'] else False,
                    "color": "#999999",
                    "wip_limit": None,
                    "order": us_status['pos'],
                })

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
        project_template.roles.append({
            "name": "Trello",
            "slug": "trello",
            "computable": False,
            "permissions": project_template.roles[0]['permissions'],
            "order": 70,
        })

        tags_colors = []
        for label in labels:
            name = label['name']
            if not name:
                name = label['color']
            name = name.lower()
            color = self._ensure_hex_color(label['color'])
            tags_colors.append([name, color])

        project = Project(
            name=options.get('name', None) or board['name'],
            description=options.get('description', None) or board['desc'],
            owner=self._user,
            tags_colors=tags_colors,
            creation_template=project_template,
            is_private=options.get('is_private', False),
        )
        (can_create, error_message) = projects_service.check_if_project_can_be_created_or_updated(project)
        if not can_create:
            raise exceptions.NotEnoughSlotsForProject(project.is_private, 1, error_message)
        project.save()

        if board.get('organization', None):
            trello_avatar_template = "https://trello-logos.s3.amazonaws.com/{}/170.png"
            project_logo_url = trello_avatar_template.format(board['organization']['logoHash'])
            data = requests.get(project_logo_url)
            project.logo.save("logo.png", ContentFile(data.content), save=True)

        UserStoryCustomAttribute.objects.create(
            name="Due",
            description="Due date",
            type="date",
            order=1,
            project=project
        )
        import_service.create_memberships(options.get('users_bindings', {}), project, self._user, "trello")
        import_service.set_base_permissions_for_project(project)
        return project

    def _import_user_stories_data(self, data, project, options):
        users_bindings = options.get('users_bindings', {})
        statuses = {s['id']: s for s in data['lists']}
        cards = data['cards']
        due_date_field = project.userstorycustomattributes.first()

        for card in cards:
            if card['closed'] and not options.get("import_closed_data", False):
                continue
            if statuses[card['idList']]['closed'] and not options.get("import_closed_data", False):
                continue

            tags = []
            for tag in card['labels']:
                name = tag['name']
                if not name:
                    name = tag['color']
                name = name.lower()
                tags.append(name)

            assigned_to = None
            if len(card['idMembers']) > 0:
                assigned_to = users_bindings.get(card['idMembers'][0], None)

            external_reference = None
            if options.get('keep_external_reference', False):
                external_reference = ["trello", card['url']]

            us = UserStory.objects.create(
                project=project,
                owner=self._user,
                assigned_to=assigned_to,
                status=project.us_statuses.get(name=statuses[card['idList']]['name']),
                kanban_order=card['pos'],
                sprint_order=card['pos'],
                backlog_order=card['pos'],
                subject=card['name'],
                description=card['desc'],
                tags=tags,
                external_reference=external_reference
            )

            if len(card['idMembers']) > 1:
                for watcher in card['idMembers'][1:]:
                    watcher_user = users_bindings.get(watcher, None)
                    if watcher_user:
                        us.add_watcher(watcher_user)

            if card['due']:
                us.custom_attributes_values.attributes_values = {due_date_field.id: card['due']}
                us.custom_attributes_values.save()

            UserStory.objects.filter(id=us.id).update(
                modified_date=card['dateLastActivity'],
                created_date=card['dateLastActivity']
            )
            self._import_attachments(us, card, options)
            self._import_tasks(data, us, card)
            self._import_actions(us, card, statuses, options)

    def _import_tasks(self, data, us, card):
        checklists_by_id = {c['id']: c for c in data['checklists']}
        for checklist_id in card['idChecklists']:
            for item in checklists_by_id.get(checklist_id, {}).get('checkItems', []):
                Task.objects.create(
                    subject=item['name'],
                    status=us.project.task_statuses.get(slug=item['state']),
                    project=us.project,
                    user_story=us
                )

    def _import_attachments(self, us, card, options):
        users_bindings = options.get('users_bindings', {})
        for attachment in card['attachments']:
            if attachment['bytes'] is None:
                continue
            data = requests.get(attachment['url'])
            att = Attachment(
                owner=users_bindings.get(attachment['idMember'], self._user),
                project=us.project,
                content_type=ContentType.objects.get_for_model(UserStory),
                object_id=us.id,
                name=attachment['name'],
                size=attachment['bytes'],
                created_date=attachment['date'],
                is_deprecated=False,
            )
            att.attached_file.save(attachment['name'], ContentFile(data.content), save=True)

            UserStory.objects.filter(id=us.id, created_date__gt=attachment['date']).update(
                created_date=attachment['date']
            )

    def _import_actions(self, us, card, statuses, options):
        included_actions = [
            "addAttachmentToCard", "addMemberToCard", "commentCard",
            "convertToCardFromCheckItem", "copyCommentCard", "createCard",
            "deleteAttachmentFromCard", "deleteCard", "removeMemberFromCard",
            "updateCard",
        ]

        actions = self._client.get(
            "/card/{}/actions".format(card['id']),
            {
                "filter": ",".join(included_actions),
                "limit": "1000",
                "memberCreator": "true",
                "memberCreator_fields": "fullName",
            }
        )

        while actions:
            for action in actions:
                self._import_action(us, action, statuses, options)
            actions = self._client.get(
                "/card/{}/actions".format(card['id']),
                {
                    "filter": ",".join(included_actions),
                    "limit": "1000",
                    "since": "lastView",
                    "before": action['date'],
                    "memberCreator": "true",
                    "memberCreator_fields": "fullName",
                }
            )

    def _import_action(self, us, action, statuses, options):
        key = make_key_from_model_object(us)
        typename = get_typename_for_model_class(UserStory)
        action_data = self._transform_action_data(us, action, statuses, options)
        if action_data is None:
            return

        change_old = action_data['change_old']
        change_new = action_data['change_new']
        hist_type = action_data['hist_type']
        comment = action_data['comment']
        user = action_data['user']

        diff = make_diff_from_dicts(change_old, change_new)
        fdiff = FrozenDiff(key, diff, {})

        entry = HistoryEntry.objects.create(
            user=user,
            project_id=us.project.id,
            key=key,
            type=hist_type,
            snapshot=None,
            diff=fdiff.diff,
            values=make_diff_values(typename, fdiff),
            comment=comment,
            comment_html=mdrender(us.project, comment),
            is_hidden=False,
            is_snapshot=False,
        )
        HistoryEntry.objects.filter(id=entry.id).update(created_at=action['date'])
        return HistoryEntry.objects.get(id=entry.id)

    def _transform_action_data(self, us, action, statuses, options):
        users_bindings = options.get('users_bindings', {})
        due_date_field = us.project.userstorycustomattributes.first()

        ignored_actions = ["addAttachmentToCard", "addMemberToCard",
                           "deleteAttachmentFromCard", "deleteCard",
                           "removeMemberFromCard"]

        if action['type'] in ignored_actions:
            return None

        user = {"pk": None, "name": action.get('memberCreator', {}).get('fullName', None)}
        taiga_user = users_bindings.get(action.get('memberCreator', {}).get('id', None), None)
        if taiga_user:
            user = {"pk": taiga_user.id, "name": taiga_user.get_full_name()}

        result = {
            "change_old": {},
            "change_new": {},
            "hist_type": HistoryType.change,
            "comment": "",
            "user": user
        }

        if action['type'] == "commentCard":
            result['comment'] = str(action['data']['text'])
        elif action['type'] == "convertToCardFromCheckItem":
            UserStory.objects.filter(id=us.id, created_date__gt=action['date']).update(
                created_date=action['date'],
                owner=users_bindings.get(action["idMemberCreator"], self._user)
            )
            result['hist_type'] = HistoryType.create
        elif action['type'] == "copyCommentCard":
            UserStory.objects.filter(id=us.id, created_date__gt=action['date']).update(
                created_date=action['date'],
                owner=users_bindings.get(action["idMemberCreator"], self._user)
            )
            result['hist_type'] = HistoryType.create
        elif action['type'] == "createCard":
            UserStory.objects.filter(id=us.id, created_date__gt=action['date']).update(
                created_date=action['date'],
                owner=users_bindings.get(action["idMemberCreator"], self._user)
            )
            result['hist_type'] = HistoryType.create
        elif action['type'] == "updateCard":
            if 'desc' in action['data']['old']:
                result['change_old']["description"] = str(action['data']['old'].get('desc', ''))
                result['change_new']["description"] = str(action['data']['card'].get('desc', ''))
                result['change_old']["description_html"] = mdrender(us.project, str(action['data']['old'].get('desc', '')))
                result['change_new']["description_html"] = mdrender(us.project, str(action['data']['card'].get('desc', '')))
            if 'idList' in action['data']['old']:
                old_status_name = statuses[action['data']['old']['idList']]['name']
                result['change_old']["status"] = us.project.us_statuses.get(name=old_status_name).id
                new_status_name = statuses[action['data']['card']['idList']]['name']
                result['change_new']["status"] = us.project.us_statuses.get(name=new_status_name).id
            if 'name' in action['data']['old']:
                result['change_old']["subject"] = action['data']['old']['name']
                result['change_new']["subject"] = action['data']['card']['name']
            if 'due' in action['data']['old']:
                result['change_old']["custom_attributes"] = [{
                    "name": "Due",
                    "value": action['data']['old']['due'],
                    "id": due_date_field.id
                }]
                result['change_new']["custom_attributes"] = [{
                    "name": "Due",
                    "value": action['data']['card']['due'],
                    "id": due_date_field.id
                }]

            if result['change_old'] == {}:
                return None
        return result

    @classmethod
    def get_auth_url(cls):
        request_token_url = 'https://trello.com/1/OAuthGetRequestToken'
        authorize_url = 'https://trello.com/1/OAuthAuthorizeToken'
        return_url = resolve_front_url("new-project-import", "trello")
        expiration = "1day"
        scope = "read,write,account"
        trello_key = settings.IMPORTERS.get('trello', {}).get('api_key', None)
        trello_secret = settings.IMPORTERS.get('trello', {}).get('secret_key', None)
        name = "Taiga"

        session = OAuth1Session(client_key=trello_key, client_secret=trello_secret)
        response = session.fetch_request_token(request_token_url)
        oauth_token, oauth_token_secret = response.get('oauth_token'), response.get('oauth_token_secret')

        return (
            oauth_token,
            oauth_token_secret,
            "{authorize_url}?oauth_token={oauth_token}&scope={scope}&expiration={expiration}&name={name}&return_url={return_url}".format(
                authorize_url=authorize_url,
                oauth_token=oauth_token,
                expiration=expiration,
                scope=scope,
                name=name,
                return_url=return_url,
            )
        )

    @classmethod
    def get_access_token(cls, oauth_token, oauth_token_secret, oauth_verifier):
        api_key = settings.IMPORTERS.get('trello', {}).get('api_key', None)
        api_secret = settings.IMPORTERS.get('trello', {}).get('secret_key', None)
        access_token_url = 'https://trello.com/1/OAuthGetAccessToken'
        session = OAuth1Session(client_key=api_key, client_secret=api_secret,
                                resource_owner_key=oauth_token, resource_owner_secret=oauth_token_secret,
                                verifier=oauth_verifier)
        access_token = session.fetch_access_token(access_token_url)
        return access_token

    def _ensure_hex_color(self, color):
        if color is None:
            return None
        try:
            return webcolors.name_to_hex(color)
        except ValueError:
            return color

    def _cleanup(self, project, options):
        if not options.get("import_closed_data", False):
            project.us_statuses.filter(is_archived=True).delete()
