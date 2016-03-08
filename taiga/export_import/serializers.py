# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import base64
import copy
import os
from collections import OrderedDict

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType


from taiga import mdrender
from taiga.base.api import serializers
from taiga.base.fields import JsonField, PgArrayField

from taiga.projects import models as projects_models
from taiga.projects.custom_attributes import models as custom_attributes_models
from taiga.projects.userstories import models as userstories_models
from taiga.projects.tasks import models as tasks_models
from taiga.projects.issues import models as issues_models
from taiga.projects.milestones import models as milestones_models
from taiga.projects.wiki import models as wiki_models
from taiga.projects.history import models as history_models
from taiga.projects.attachments import models as attachments_models
from taiga.timeline import models as timeline_models
from taiga.users import models as users_models
from taiga.projects.notifications import services as notifications_services
from taiga.projects.votes import services as votes_service
from taiga.projects.history import services as history_service


class FileField(serializers.WritableField):
    read_only = False

    def to_native(self, obj):
        if not obj:
            return None

        data = base64.b64encode(obj.read()).decode('utf-8')

        return OrderedDict([
            ("data", data),
            ("name", os.path.basename(obj.name)),
        ])

    def from_native(self, data):
        if not data:
            return None

        decoded_data = b''
        # The original file was encoded by chunks but we don't really know its
        # length or if it was multiple of 3 so we must iterate over all those chunks
        # decoding them one by one
        for decoding_chunk in data['data'].split("="):
            # When encoding to base64 3 bytes are transformed into 4 bytes and
            # the extra space of the block is filled with =
            # We must ensure that the decoding chunk has a length multiple of 4 so
            # we restore the stripped '='s adding appending them until the chunk has
            # a length multiple of 4
            decoding_chunk += "=" * (-len(decoding_chunk) % 4)
            decoded_data += base64.b64decode(decoding_chunk+"=")

        return ContentFile(decoded_data, name=data['name'])


class RelatedNoneSafeField(serializers.RelatedField):
    def field_from_native(self, data, files, field_name, into):
        if self.read_only:
            return

        try:
            if self.many:
                try:
                    # Form data
                    value = data.getlist(field_name)
                    if value == [''] or value == []:
                        raise KeyError
                except AttributeError:
                    # Non-form data
                    value = data[field_name]
            else:
                value = data[field_name]
        except KeyError:
            if self.partial:
                return
            value = self.get_default_value()

        key = self.source or field_name
        if value in self.null_values:
            if self.required:
                raise ValidationError(self.error_messages['required'])
            into[key] = None
        elif self.many:
            into[key] = [self.from_native(item) for item in value if self.from_native(item) is not None]
        else:
            into[key] = self.from_native(value)


class UserRelatedField(RelatedNoneSafeField):
    read_only = False

    def to_native(self, obj):
        if obj:
            return obj.email
        return None

    def from_native(self, data):
        try:
            return users_models.User.objects.get(email=data)
        except users_models.User.DoesNotExist:
            return None


class UserPkField(serializers.RelatedField):
    read_only = False

    def to_native(self, obj):
        try:
            user = users_models.User.objects.get(pk=obj)
            return user.email
        except users_models.User.DoesNotExist:
            return None

    def from_native(self, data):
        try:
            user = users_models.User.objects.get(email=data)
            return user.pk
        except users_models.User.DoesNotExist:
            return None


class CommentField(serializers.WritableField):
    read_only = False

    def field_from_native(self, data, files, field_name, into):
        super().field_from_native(data, files, field_name, into)
        into["comment_html"] = mdrender.render(self.context['project'], data.get("comment", ""))


class ProjectRelatedField(serializers.RelatedField):
    read_only = False

    def __init__(self, slug_field, *args, **kwargs):
        self.slug_field = slug_field
        super().__init__(*args, **kwargs)

    def to_native(self, obj):
        if obj:
            return getattr(obj, self.slug_field)
        return None

    def from_native(self, data):
        try:
            kwargs = {self.slug_field: data, "project": self.context['project']}
            return self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise ValidationError(_("{}=\"{}\" not found in this project".format(self.slug_field, data)))


class HistoryUserField(JsonField):
    def to_native(self, obj):
        if obj is None or obj == {}:
            return []
        try:
            user = users_models.User.objects.get(pk=obj['pk'])
        except users_models.User.DoesNotExist:
            user = None
        return (UserRelatedField().to_native(user), obj['name'])

    def from_native(self, data):
        if data is None:
            return {}

        if len(data) < 2:
            return {}

        user = UserRelatedField().from_native(data[0])

        if user:
            pk = user.pk
        else:
            pk = None

        return {"pk": pk, "name": data[1]}


class HistoryValuesField(JsonField):
    def to_native(self, obj):
        if obj is None:
            return []
        if "users" in obj:
            obj['users'] = list(map(UserPkField().to_native, obj['users']))
        return obj

    def from_native(self, data):
        if data is None:
            return []
        if "users" in data:
            data['users'] = list(map(UserPkField().from_native, data['users']))
        return data


class HistoryDiffField(JsonField):
    def to_native(self, obj):
        if obj is None:
            return []

        if "assigned_to" in obj:
            obj['assigned_to'] = list(map(UserPkField().to_native, obj['assigned_to']))

        return obj

    def from_native(self, data):
        if data is None:
            return []

        if "assigned_to" in data:
            data['assigned_to'] = list(map(UserPkField().from_native, data['assigned_to']))
        return data


class WatcheableObjectModelSerializer(serializers.ModelSerializer):
    watchers = UserRelatedField(many=True, required=False)

    def __init__(self, *args, **kwargs):
        self._watchers_field = self.base_fields.pop("watchers", None)
        super(WatcheableObjectModelSerializer, self).__init__(*args, **kwargs)

    """
    watchers is not a field from the model so we need to do some magic to make it work like a normal field
    It's supposed to be represented as an email list but internally it's treated like notifications.Watched instances
    """

    def restore_object(self, attrs, instance=None):
        watcher_field = self.fields.pop("watchers", None)
        instance = super(WatcheableObjectModelSerializer, self).restore_object(attrs, instance)
        self._watchers = self.init_data.get("watchers", [])
        return instance

    def save_watchers(self):
        new_watcher_emails = set(self._watchers)
        old_watcher_emails = set(self.object.get_watchers().values_list("email", flat=True))
        adding_watcher_emails = list(new_watcher_emails.difference(old_watcher_emails))
        removing_watcher_emails = list(old_watcher_emails.difference(new_watcher_emails))

        User = apps.get_model("users", "User")
        adding_users = User.objects.filter(email__in=adding_watcher_emails)
        removing_users = User.objects.filter(email__in=removing_watcher_emails)

        for user in adding_users:
            notifications_services.add_watcher(self.object, user)

        for user in removing_users:
            notifications_services.remove_watcher(self.object, user)

        self.object.watchers = [user.email for user in self.object.get_watchers()]

    def to_native(self, obj):
        ret = super(WatcheableObjectModelSerializer, self).to_native(obj)
        ret["watchers"] = [user.email for user in obj.get_watchers()]
        return ret


class HistoryExportSerializer(serializers.ModelSerializer):
    user = HistoryUserField()
    diff = HistoryDiffField(required=False)
    snapshot = JsonField(required=False)
    values = HistoryValuesField(required=False)
    comment = CommentField(required=False)
    delete_comment_date = serializers.DateTimeField(required=False)
    delete_comment_user = HistoryUserField(required=False)

    class Meta:
        model = history_models.HistoryEntry
        exclude = ("id", "comment_html", "key")


class HistoryExportSerializerMixin(serializers.ModelSerializer):
    history = serializers.SerializerMethodField("get_history")

    def get_history(self, obj):
        history_qs = history_service.get_history_queryset_by_model_instance(obj,
            types=(history_models.HistoryType.change, history_models.HistoryType.create,))

        return HistoryExportSerializer(history_qs, many=True).data


class AttachmentExportSerializer(serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    attached_file = FileField()
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = attachments_models.Attachment
        exclude = ('id', 'content_type', 'object_id', 'project')


class AttachmentExportSerializerMixin(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField("get_attachments")

    def get_attachments(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        attachments_qs = attachments_models.Attachment.objects.filter(object_id=obj.pk,
                                                                      content_type=content_type)
        return AttachmentExportSerializer(attachments_qs, many=True).data


class PointsExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.Points
        exclude = ('id', 'project')


class UserStoryStatusExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.UserStoryStatus
        exclude = ('id', 'project')


class TaskStatusExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.TaskStatus
        exclude = ('id', 'project')


class IssueStatusExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.IssueStatus
        exclude = ('id', 'project')


class PriorityExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.Priority
        exclude = ('id', 'project')


class SeverityExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.Severity
        exclude = ('id', 'project')


class IssueTypeExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.IssueType
        exclude = ('id', 'project')


class RoleExportSerializer(serializers.ModelSerializer):
    permissions = PgArrayField(required=False)

    class Meta:
        model = users_models.Role
        exclude = ('id', 'project')


class UserStoryCustomAttributeExportSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.UserStoryCustomAttribute
        exclude = ('id', 'project')


class TaskCustomAttributeExportSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.TaskCustomAttribute
        exclude = ('id', 'project')


class IssueCustomAttributeExportSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.IssueCustomAttribute
        exclude = ('id', 'project')


class CustomAttributesValuesExportSerializerMixin(serializers.ModelSerializer):
    custom_attributes_values = serializers.SerializerMethodField("get_custom_attributes_values")

    def custom_attributes_queryset(self, project):
        raise NotImplementedError()

    def get_custom_attributes_values(self, obj):
        def _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values):
            ret = {}
            for attr in custom_attributes:
                value = values.get(str(attr["id"]), None)
                if value is not  None:
                    ret[attr["name"]] = value

            return ret

        try:
            values =  obj.custom_attributes_values.attributes_values
            custom_attributes = self.custom_attributes_queryset(obj.project).values('id', 'name')

            return _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values)
        except ObjectDoesNotExist:
            return None


class BaseCustomAttributesValuesExportSerializer(serializers.ModelSerializer):
    attributes_values = JsonField(source="attributes_values",required=True)
    _custom_attribute_model = None
    _container_field = None

    class Meta:
        exclude = ("id",)

    def validate_attributes_values(self, attrs, source):
        # values must be a dict
        data_values = attrs.get("attributes_values", None)
        if self.object:
            data_values = (data_values or self.object.attributes_values)

        if type(data_values) is not dict:
            raise ValidationError(_("Invalid content. It must be {\"key\": \"value\",...}"))

        # Values keys must be in the container object project
        data_container = attrs.get(self._container_field, None)
        if data_container:
            project_id = data_container.project_id
        elif self.object:
            project_id = getattr(self.object, self._container_field).project_id
        else:
            project_id = None

        values_ids = list(data_values.keys())
        qs = self._custom_attribute_model.objects.filter(project=project_id,
                                                         id__in=values_ids)
        if qs.count() != len(values_ids):
            raise ValidationError(_("It contain invalid custom fields."))

        return attrs

class UserStoryCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    _custom_attribute_model = custom_attributes_models.UserStoryCustomAttribute
    _container_model = "userstories.UserStory"
    _container_field = "user_story"

    class Meta(BaseCustomAttributesValuesExportSerializer.Meta):
        model = custom_attributes_models.UserStoryCustomAttributesValues


class TaskCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    _custom_attribute_model = custom_attributes_models.TaskCustomAttribute
    _container_field = "task"

    class Meta(BaseCustomAttributesValuesExportSerializer.Meta):
        model = custom_attributes_models.TaskCustomAttributesValues


class IssueCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    _custom_attribute_model = custom_attributes_models.IssueCustomAttribute
    _container_field = "issue"

    class Meta(BaseCustomAttributesValuesExportSerializer.Meta):
        model = custom_attributes_models.IssueCustomAttributesValues


class MembershipExportSerializer(serializers.ModelSerializer):
    user = UserRelatedField(required=False)
    role = ProjectRelatedField(slug_field="name")
    invited_by = UserRelatedField(required=False)

    class Meta:
        model = projects_models.Membership
        exclude = ('id', 'project', 'token')

    def full_clean(self, instance):
        return instance


class RolePointsExportSerializer(serializers.ModelSerializer):
    role = ProjectRelatedField(slug_field="name")
    points = ProjectRelatedField(slug_field="name")

    class Meta:
        model = userstories_models.RolePoints
        exclude = ('id', 'user_story')


class MilestoneExportSerializer(WatcheableObjectModelSerializer):
    owner = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)
    estimated_start = serializers.DateField(required=False)
    estimated_finish = serializers.DateField(required=False)

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super(MilestoneExportSerializer, self).__init__(*args, **kwargs)
        if project:
            self.project = project

    def validate_name(self, attrs, source):
        """
        Check the milestone name is not duplicated in the project
        """
        name = attrs[source]
        qs = self.project.milestones.filter(name=name)
        if qs.exists():
            raise serializers.ValidationError(_("Name duplicated for the project"))

        return attrs

    class Meta:
        model = milestones_models.Milestone
        exclude = ('id', 'project')


class TaskExportSerializer(CustomAttributesValuesExportSerializerMixin, HistoryExportSerializerMixin,
                           AttachmentExportSerializerMixin, WatcheableObjectModelSerializer):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    user_story = ProjectRelatedField(slug_field="ref", required=False)
    milestone = ProjectRelatedField(slug_field="name", required=False)
    assigned_to = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = tasks_models.Task
        exclude = ('id', 'project')

    def custom_attributes_queryset(self, project):
        return project.taskcustomattributes.all()


class UserStoryExportSerializer(CustomAttributesValuesExportSerializerMixin, HistoryExportSerializerMixin,
                                AttachmentExportSerializerMixin, WatcheableObjectModelSerializer):
    role_points = RolePointsExportSerializer(many=True, required=False)
    owner = UserRelatedField(required=False)
    assigned_to = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    milestone = ProjectRelatedField(slug_field="name", required=False)
    modified_date = serializers.DateTimeField(required=False)
    generated_from_issue = ProjectRelatedField(slug_field="ref", required=False)

    class Meta:
        model = userstories_models.UserStory
        exclude = ('id', 'project', 'points', 'tasks')

    def custom_attributes_queryset(self, project):
        return project.userstorycustomattributes.all()


class IssueExportSerializer(CustomAttributesValuesExportSerializerMixin, HistoryExportSerializerMixin,
                            AttachmentExportSerializerMixin, WatcheableObjectModelSerializer):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    assigned_to = UserRelatedField(required=False)
    priority = ProjectRelatedField(slug_field="name")
    severity = ProjectRelatedField(slug_field="name")
    type = ProjectRelatedField(slug_field="name")
    milestone = ProjectRelatedField(slug_field="name", required=False)
    votes = serializers.SerializerMethodField("get_votes")
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = issues_models.Issue
        exclude = ('id', 'project')

    def get_votes(self, obj):
        return [x.email for x in votes_service.get_voters(obj)]

    def custom_attributes_queryset(self, project):
        return project.issuecustomattributes.all()


class WikiPageExportSerializer(HistoryExportSerializerMixin, AttachmentExportSerializerMixin,
                               WatcheableObjectModelSerializer):
    owner = UserRelatedField(required=False)
    last_modifier = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = wiki_models.WikiPage
        exclude = ('id', 'project')


class WikiLinkExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = wiki_models.WikiLink
        exclude = ('id', 'project')



class TimelineDataField(serializers.WritableField):
    read_only = False

    def to_native(self, data):
        new_data = copy.deepcopy(data)
        try:
            user = users_models.User.objects.get(pk=new_data["user"]["id"])
            new_data["user"]["email"] = user.email
            del new_data["user"]["id"]
        except users_models.User.DoesNotExist:
            pass
        return new_data

    def from_native(self, data):
        new_data = copy.deepcopy(data)
        try:
            user = users_models.User.objects.get(email=new_data["user"]["email"])
            new_data["user"]["id"] = user.id
            del new_data["user"]["email"]
        except users_models.User.DoesNotExist:
            pass

        return new_data


class TimelineExportSerializer(serializers.ModelSerializer):
    data = TimelineDataField()
    class Meta:
        model = timeline_models.Timeline
        exclude = ('id', 'project', 'namespace', 'object_id')


class ProjectExportSerializer(WatcheableObjectModelSerializer):
    logo = FileField(required=False)
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    modified_date = serializers.DateTimeField(required=False)
    roles = RoleExportSerializer(many=True, required=False)
    owner = UserRelatedField(required=False)
    memberships = MembershipExportSerializer(many=True, required=False)
    points = PointsExportSerializer(many=True, required=False)
    us_statuses = UserStoryStatusExportSerializer(many=True, required=False)
    task_statuses = TaskStatusExportSerializer(many=True, required=False)
    issue_types = IssueTypeExportSerializer(many=True, required=False)
    issue_statuses = IssueStatusExportSerializer(many=True, required=False)
    priorities = PriorityExportSerializer(many=True, required=False)
    severities = SeverityExportSerializer(many=True, required=False)
    tags_colors = JsonField(required=False)
    default_points = serializers.SlugRelatedField(slug_field="name", required=False)
    default_us_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_task_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_priority = serializers.SlugRelatedField(slug_field="name", required=False)
    default_severity = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_type = serializers.SlugRelatedField(slug_field="name", required=False)
    userstorycustomattributes = UserStoryCustomAttributeExportSerializer(many=True, required=False)
    taskcustomattributes = TaskCustomAttributeExportSerializer(many=True, required=False)
    issuecustomattributes = IssueCustomAttributeExportSerializer(many=True, required=False)
    user_stories = UserStoryExportSerializer(many=True, required=False)
    tasks = TaskExportSerializer(many=True, required=False)
    milestones = MilestoneExportSerializer(many=True, required=False)
    issues = IssueExportSerializer(many=True, required=False)
    wiki_links = WikiLinkExportSerializer(many=True, required=False)
    wiki_pages = WikiPageExportSerializer(many=True, required=False)

    class Meta:
        model = projects_models.Project
        exclude = ('id', 'creation_template', 'members')
