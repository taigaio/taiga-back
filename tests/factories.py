# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid
import threading
from datetime import date, timedelta

from django.conf import settings

from .utils import DUMMY_BMP_DATA

import factory

from taiga.permissions.choices import MEMBERS_PERMISSIONS



class Factory(factory.django.DjangoModelFactory):
    class Meta:
        strategy = factory.CREATE_STRATEGY
        model = None
        abstract = True

    _SEQUENCE = 1
    _SEQUENCE_LOCK = threading.Lock()

    @classmethod
    def _setup_next_sequence(cls):
        with cls._SEQUENCE_LOCK:
            cls._SEQUENCE += 1
        return cls._SEQUENCE


class ProjectTemplateFactory(Factory):
    class Meta:
        strategy = factory.CREATE_STRATEGY
        model = "projects.ProjectTemplate"
        django_get_or_create = ("slug",)

    name = "Template name"
    slug = settings.DEFAULT_PROJECT_TEMPLATE
    description = factory.Sequence(lambda n: "Description {}".format(n))

    epic_statuses = []
    us_statuses = []
    us_duedates = []
    points = []
    task_statuses = []
    task_duedates = []
    issue_statuses = []
    issue_types = []
    issue_duedates = []
    priorities = []
    severities = []
    roles = []
    epic_custom_attributes = []
    us_custom_attributes = []
    task_custom_attributes = []
    issue_custom_attributes = []
    default_owner_role = "tester"


class ProjectFactory(Factory):
    class Meta:
        model = "projects.Project"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Project {}".format(n))
    slug = factory.Sequence(lambda n: "project-{}-slug".format(n))
    logo = factory.django.FileField(data=DUMMY_BMP_DATA)

    description = "Project description"
    owner = factory.SubFactory("tests.factories.UserFactory")
    creation_template = factory.SubFactory("tests.factories.ProjectTemplateFactory")


class ProjectModulesConfigFactory(Factory):
    class Meta:
        model = "projects.ProjectModulesConfig"
        strategy = factory.CREATE_STRATEGY

    project = factory.SubFactory("tests.factories.ProjectFactory")


class RoleFactory(Factory):
    class Meta:
        model = "users.Role"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Role {}".format(n))
    slug = factory.Sequence(lambda n: "test-role-{}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class PointsFactory(Factory):
    class Meta:
        model = "projects.Points"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Points {}".format(n))
    value = 2
    project = factory.SubFactory("tests.factories.ProjectFactory")


class SwimlaneFactory(Factory):
    class Meta:
        model = "projects.Swimlane"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Swimlane {}".format(n))
    order = factory.Sequence(lambda n: n)
    project = factory.SubFactory("tests.factories.ProjectFactory")


class RolePointsFactory(Factory):
    class Meta:
        model = "userstories.RolePoints"
        strategy = factory.CREATE_STRATEGY

    user_story = factory.SubFactory("tests.factories.UserStoryFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    points = factory.SubFactory("tests.factories.PointsFactory")


class EpicAttachmentFactory(Factory):
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    content_object = factory.SubFactory("tests.factories.EpicFactory")
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Epic Attachment {}".format(n))

    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY


class UserStoryAttachmentFactory(Factory):
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    content_object = factory.SubFactory("tests.factories.UserStoryFactory")
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "User Story Attachment {}".format(n))

    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY


class TaskAttachmentFactory(Factory):
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    content_object = factory.SubFactory("tests.factories.TaskFactory")
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Task Attachment {}".format(n))

    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY


class IssueAttachmentFactory(Factory):
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    content_object = factory.SubFactory("tests.factories.IssueFactory")
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Issue Attachment {}".format(n))

    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY


class WikiAttachmentFactory(Factory):
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    content_object = factory.SubFactory("tests.factories.WikiPageFactory")
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Wiki Attachment {}".format(n))

    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY


class UserFactory(Factory):
    class Meta:
        model = settings.AUTH_USER_MODEL
        strategy = factory.CREATE_STRATEGY

    username = factory.Sequence(lambda n: "user{}".format(n))
    email = factory.LazyAttribute(lambda obj: '%s@email.com' % obj.username)
    password = factory.PostGeneration(lambda obj, *args, **kwargs: obj.set_password(obj.username))
    accepted_terms = True
    read_new_terms = True


class MembershipFactory(Factory):
    class Meta:
        model = "projects.Membership"
        strategy = factory.CREATE_STRATEGY

    token = factory.LazyAttribute(lambda obj: str(uuid.uuid1()))
    project = factory.SubFactory("tests.factories.ProjectFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class InvitationFactory(Factory):
    class Meta:
        model = "projects.Membership"
        strategy = factory.CREATE_STRATEGY

    token = factory.LazyAttribute(lambda obj: str(uuid.uuid1()))
    project = factory.SubFactory("tests.factories.ProjectFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    email = factory.Sequence(lambda n: "user{}@email.com".format(n))


class WebhookFactory(Factory):
    class Meta:
        model = "webhooks.Webhook"
        strategy = factory.CREATE_STRATEGY

    project = factory.SubFactory("tests.factories.ProjectFactory")
    url = "http://localhost:8080/test"
    key = "factory-key"
    name = "Factory-name"


class WebhookLogFactory(Factory):
    class Meta:
        model = "webhooks.WebhookLog"
        strategy = factory.CREATE_STRATEGY

    webhook = factory.SubFactory("tests.factories.WebhookFactory")
    url = "http://localhost:8080/test"
    status = "200"
    request_data = {"text": "test-request-data"}
    response_data = {"text": "test-response-data"}


class StorageEntryFactory(Factory):
    class Meta:
        model = "userstorage.StorageEntry"
        strategy = factory.CREATE_STRATEGY

    owner = factory.SubFactory("tests.factories.UserFactory")
    key = factory.Sequence(lambda n: "key-{}".format(n))
    value = factory.Sequence(lambda n: {"value": "value-{}".format(n)})


class EpicFactory(Factory):
    class Meta:
        model = "epics.Epic"
        strategy = factory.CREATE_STRATEGY

    ref = factory.Sequence(lambda n: n)
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    subject = factory.Sequence(lambda n: "Epic {}".format(n))
    description = factory.Sequence(lambda n: "Epic {} description".format(n))
    status = factory.SubFactory("tests.factories.EpicStatusFactory")


class RelatedUserStory(Factory):
    class Meta:
        model = "epics.RelatedUserStory"
        strategy = factory.CREATE_STRATEGY

    epic = factory.SubFactory("tests.factories.EpicFactory")
    user_story = factory.SubFactory("tests.factories.UserStoryFactory")


class MilestoneFactory(Factory):
    class Meta:
        model = "milestones.Milestone"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Milestone {}".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    estimated_start = factory.LazyAttribute(lambda o: date.today())
    estimated_finish = factory.LazyAttribute(lambda o: o.estimated_start + timedelta(days=7))


class UserStoryFactory(Factory):
    class Meta:
        model = "userstories.UserStory"
        strategy = factory.CREATE_STRATEGY

    ref = factory.Sequence(lambda n: n)
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    subject = factory.Sequence(lambda n: "User Story {}".format(n))
    description = factory.Sequence(lambda n: "User Story {} description".format(n))
    status = factory.SubFactory("tests.factories.UserStoryStatusFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")
    tags = factory.Faker("words")
    due_date = factory.LazyAttribute(lambda o: date.today() + timedelta(days=7))
    due_date_reason = factory.Faker("words")

    @factory.post_generation
    def assigned_users(self, create, users_list, **kwargs):
        if not create:
            return

        if users_list:
            for user in users_list:
                self.assigned_users.add(user)


class TaskFactory(Factory):
    class Meta:
        model = "tasks.Task"
        strategy = factory.CREATE_STRATEGY

    ref = factory.Sequence(lambda n: n)
    subject = factory.Sequence(lambda n: "Task {}".format(n))
    description = factory.Sequence(lambda n: "Task {} description".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    status = factory.SubFactory("tests.factories.TaskStatusFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")
    user_story = factory.SubFactory("tests.factories.UserStoryFactory")
    tags = factory.Faker("words")
    due_date = factory.LazyAttribute(lambda o: date.today() + timedelta(days=7))
    due_date_reason = factory.Faker("words")


class IssueFactory(Factory):
    class Meta:
        model = "issues.Issue"
        strategy = factory.CREATE_STRATEGY

    ref = factory.Sequence(lambda n: n)
    subject = factory.Sequence(lambda n: "Issue {}".format(n))
    description = factory.Sequence(lambda n: "Issue {} description".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    status = factory.SubFactory("tests.factories.IssueStatusFactory")
    severity = factory.SubFactory("tests.factories.SeverityFactory")
    priority = factory.SubFactory("tests.factories.PriorityFactory")
    type = factory.SubFactory("tests.factories.IssueTypeFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")
    tags = factory.Faker("words")
    due_date = factory.LazyAttribute(lambda o: date.today() + timedelta(days=7))
    due_date_reason = factory.Faker("words")


class WikiPageFactory(Factory):
    class Meta:
        model = "wiki.WikiPage"
        strategy = factory.CREATE_STRATEGY

    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    slug = factory.Sequence(lambda n: "wiki-page-{}".format(n))
    content = factory.Sequence(lambda n: "Wiki Page {} content".format(n))


class WikiLinkFactory(Factory):
    class Meta:
        model = "wiki.WikiLink"
        strategy = factory.CREATE_STRATEGY

    project = factory.SubFactory("tests.factories.ProjectFactory")
    title = factory.Sequence(lambda n: "Wiki Link {} title".format(n))
    href = factory.Sequence(lambda n: "link-{}".format(n))
    order = factory.Sequence(lambda n: n)


class EpicStatusFactory(Factory):
    class Meta:
        model = "projects.EpicStatus"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Epic status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class UserStoryStatusFactory(Factory):
    class Meta:
        model = "projects.UserStoryStatus"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "User Story status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class UserStoryDueDateFactory(Factory):
    class Meta:
        model = "projects.UserStoryDueDate"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "User Story due date {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class TaskStatusFactory(Factory):
    class Meta:
        model = "projects.TaskStatus"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Task status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class IssueStatusFactory(Factory):
    class Meta:
        model = "projects.IssueStatus"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Issue Status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class SeverityFactory(Factory):
    class Meta:
        model = "projects.Severity"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Severity {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class PriorityFactory(Factory):
    class Meta:
        model = "projects.Priority"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Priority {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class IssueTypeFactory(Factory):
    class Meta:
        model = "projects.IssueType"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Issue Type {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class EpicCustomAttributeFactory(Factory):
    class Meta:
        model = "custom_attributes.EpicCustomAttribute"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Epic Custom Attribute {}".format(n))
    description = factory.Sequence(lambda n: "Description for Epic Custom Attribute {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class UserStoryCustomAttributeFactory(Factory):
    class Meta:
        model = "custom_attributes.UserStoryCustomAttribute"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "UserStory Custom Attribute {}".format(n))
    description = factory.Sequence(lambda n: "Description for UserStory Custom Attribute {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class TaskCustomAttributeFactory(Factory):
    class Meta:
        model = "custom_attributes.TaskCustomAttribute"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Task Custom Attribute {}".format(n))
    description = factory.Sequence(lambda n: "Description for Task Custom Attribute {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class IssueCustomAttributeFactory(Factory):
    class Meta:
        model = "custom_attributes.IssueCustomAttribute"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Issue Custom Attribute {}".format(n))
    description = factory.Sequence(lambda n: "Description for Issue Custom Attribute {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class EpicCustomAttributesValuesFactory(Factory):
    class Meta:
        model = "custom_attributes.EpicCustomAttributesValues"
        strategy = factory.CREATE_STRATEGY

    attributes_values = {}
    epic = factory.SubFactory("tests.factories.EpicFactory")


class UserStoryCustomAttributesValuesFactory(Factory):
    class Meta:
        model = "custom_attributes.UserStoryCustomAttributesValues"
        strategy = factory.CREATE_STRATEGY

    attributes_values = {}
    user_story = factory.SubFactory("tests.factories.UserStoryFactory")


class TaskCustomAttributesValuesFactory(Factory):
    class Meta:
        model = "custom_attributes.TaskCustomAttributesValues"
        strategy = factory.CREATE_STRATEGY

    attributes_values = {}
    task = factory.SubFactory("tests.factories.TaskFactory")


class IssueCustomAttributesValuesFactory(Factory):
    class Meta:
        model = "custom_attributes.IssueCustomAttributesValues"
        strategy = factory.CREATE_STRATEGY

    attributes_values = {}
    issue = factory.SubFactory("tests.factories.IssueFactory")


class LikeFactory(Factory):
    class Meta:
        model = "likes.Like"
        strategy = factory.CREATE_STRATEGY

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    user = factory.SubFactory("tests.factories.UserFactory")


class VoteFactory(Factory):
    class Meta:
        model = "votes.Vote"
        strategy = factory.CREATE_STRATEGY

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    user = factory.SubFactory("tests.factories.UserFactory")


class VotesFactory(Factory):
    class Meta:
        model = "votes.Votes"
        strategy = factory.CREATE_STRATEGY

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)


class WatchedFactory(Factory):
    class Meta:
        model = "notifications.Watched"
        strategy = factory.CREATE_STRATEGY

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    user = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")


class ContentTypeFactory(Factory):
    class Meta:
        model = "contenttypes.ContentType"
        strategy = factory.CREATE_STRATEGY
        django_get_or_create = ("app_label", "model")

    app_label = factory.LazyAttribute(lambda obj: "issues")
    model = factory.LazyAttribute(lambda obj: "Issue")


class AttachmentFactory(Factory):
    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY

    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Attachment {}".format(n))


class HistoryEntryFactory(Factory):
    class Meta:
        model = "history.HistoryEntry"
        strategy = factory.CREATE_STRATEGY

    type = 1


class ApplicationFactory(Factory):
    class Meta:
        model = "external_apps.Application"
        strategy = factory.CREATE_STRATEGY


class ApplicationTokenFactory(Factory):
    class Meta:
        model = "external_apps.ApplicationToken"
        strategy = factory.CREATE_STRATEGY

    application = factory.SubFactory("tests.factories.ApplicationFactory")
    user = factory.SubFactory("tests.factories.UserFactory")

def create_issue(**kwargs):
    "Create an issue and along with its dependencies."
    owner = kwargs.pop("owner", None)
    if owner is None:
        owner = UserFactory.create()

    project = kwargs.pop("project", None)
    if project is None:
        project = ProjectFactory.create(owner=owner)

    defaults = {
        "project": project,
        "owner": owner,
        "status": IssueStatusFactory.create(project=project),
        "milestone": MilestoneFactory.create(project=project),
        "priority": PriorityFactory.create(project=project),
        "severity": SeverityFactory.create(project=project),
        "type": IssueTypeFactory.create(project=project),
    }
    defaults.update(kwargs)

    return IssueFactory.create(**defaults)


class Missing:
    pass


def create_task(**kwargs):
    "Create a task and along with its dependencies."
    owner = kwargs.pop("owner", None)
    if not owner:
        owner = UserFactory.create()

    project = kwargs.pop("project", None)
    if project is None:
        project = ProjectFactory.create(owner=owner)

    status = kwargs.pop("status", None)
    milestone = kwargs.pop("milestone", None)

    defaults = {
        "project": project,
        "owner": owner,
        "status": status or TaskStatusFactory.create(project=project),
        "milestone": milestone or MilestoneFactory.create(project=project),
    }

    user_story = kwargs.pop("user_story", Missing)

    defaults["user_story"] = (
        UserStoryFactory.create(project=project, owner=owner, milestone=defaults["milestone"])
        if user_story is Missing
        else user_story
    )
    defaults.update(kwargs)

    return TaskFactory.create(**defaults)


def create_membership(**kwargs):
    "Create a membership along with its dependencies"
    project = kwargs.pop("project", ProjectFactory())
    project.points.add(PointsFactory.create(project=project, value=None))

    defaults = {
        "project": project,
        "user": UserFactory.create(),
        "role": RoleFactory.create(project=project,
                                   permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    }
    defaults.update(kwargs)

    return MembershipFactory.create(**defaults)


def create_invitation(**kwargs):
    "Create an invitation along with its dependencies"
    project = kwargs.pop("project", ProjectFactory())
    project.points.add(PointsFactory.create(project=project, value=None))

    defaults = {
        "project": project,
        "role": RoleFactory.create(project=project),
        "email": "invited-user@email.com",
        "token": "tokenvalue",
        "invited_by_id": project.owner.id
    }
    defaults.update(kwargs)

    return MembershipFactory.create(**defaults)


def create_userstory(**kwargs):
    """Create an user story along with its dependencies"""
    owner = kwargs.pop("owner", None)
    if not owner:
        owner = UserFactory.create()

    project = kwargs.pop("project", None)
    if project is None:
        project = ProjectFactory.create(owner=owner)
    project.default_points = PointsFactory.create(project=project)

    defaults = {
        "project": project,
        "owner": owner,
        "milestone": MilestoneFactory.create(project=project, owner=owner)
    }
    defaults.update(kwargs)

    return UserStoryFactory(**defaults)


def create_epic(**kwargs):
    "Create an epic along with its dependencies"

    owner = kwargs.pop("owner", None)
    if not owner:
        owner = UserFactory.create()

    project = kwargs.pop("project", None)
    if project is None:
        project = ProjectFactory.create(owner=owner)

    defaults = {
        "project": project,
        "owner": owner,
    }
    defaults.update(kwargs)

    return EpicFactory(**defaults)


def create_project(**kwargs):
    "Create a project along with its dependencies"
    defaults = {}
    defaults.update(kwargs)

    ProjectTemplateFactory.create(slug=settings.DEFAULT_PROJECT_TEMPLATE)

    project = ProjectFactory.create(**defaults)
    project.default_issue_status = IssueStatusFactory.create(project=project)
    project.default_severity = SeverityFactory.create(project=project)
    project.default_priority = PriorityFactory.create(project=project)
    project.default_issue_type = IssueTypeFactory.create(project=project)
    project.default_us_status = UserStoryStatusFactory.create(project=project)
    project.default_task_status = TaskStatusFactory.create(project=project)
    project.default_epic_status = EpicStatusFactory.create(project=project)
    project.default_points = PointsFactory.create(project=project)

    project.save()

    return project


def create_swimlane(**kwargs):
    "Create a swimlane along with its dependencies."

    project = kwargs.pop("project", None)
    if project is None:
        project = ProjectFactory.create()

    defaults = {
        "project": project,
    }
    defaults.update(kwargs)

    return SwimlaneFactory.create(**defaults)


def create_user(**kwargs):
    "Create an user along with her dependencies"
    ProjectTemplateFactory.create(slug=settings.DEFAULT_PROJECT_TEMPLATE)
    RoleFactory.create()
    return UserFactory.create(**kwargs)
