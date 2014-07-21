# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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

import uuid
import threading
from datetime import date, timedelta

from django.db.models.loading import get_model

import factory
from django.conf import settings


class Factory(factory.DjangoModelFactory):
    FACTORY_STRATEGY = factory.CREATE_STRATEGY

    _SEQUENCE = 1
    _SEQUENCE_LOCK = threading.Lock()

    @classmethod
    def _setup_next_sequence(cls):
        with cls._SEQUENCE_LOCK:
            cls._SEQUENCE += 1
        return cls._SEQUENCE


class ProjectTemplateFactory(Factory):
    FACTORY_FOR = get_model("projects", "ProjectTemplate")
    FACTORY_DJANGO_GET_OR_CREATE = ("slug", )

    name = "Template name"
    slug = settings.DEFAULT_PROJECT_TEMPLATE

    us_statuses = []
    points = []
    task_statuses = []
    issue_statuses = []
    issue_types = []
    priorities = []
    severities = []
    roles = []


class ProjectFactory(Factory):
    FACTORY_FOR = get_model("projects", "Project")

    name = factory.Sequence(lambda n: "Project {}".format(n))
    slug = factory.Sequence(lambda n: "project-{}-slug".format(n))
    description = "Project description"
    owner = factory.SubFactory("tests.factories.UserFactory")
    creation_template = factory.SubFactory("tests.factories.ProjectTemplateFactory")


class RoleFactory(Factory):
    FACTORY_FOR = get_model("users", "Role")

    name = "Tester"
    project = factory.SubFactory("tests.factories.ProjectFactory")


class PointsFactory(Factory):
    FACTORY_FOR = get_model("projects", "Points")

    name = factory.Sequence(lambda n: "Points {}".format(n))
    value = 2
    project = factory.SubFactory("tests.factories.ProjectFactory")


class RolePointsFactory(Factory):
    FACTORY_FOR = get_model("userstories", "RolePoints")

    user_story = factory.SubFactory("tests.factories.UserStoryFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    points = factory.SubFactory("tests.factories.PointsFactory")


class UserFactory(Factory):
    FACTORY_FOR = get_model("users", "User")

    username = factory.Sequence(lambda n: "user{}".format(n))
    email = factory.LazyAttribute(lambda obj: '%s@email.com' % obj.username)
    password = factory.PostGeneration(lambda obj, *args, **kwargs: obj.set_password(obj.username))


class MembershipFactory(Factory):
    FACTORY_FOR = get_model("projects", "Membership")

    token = factory.LazyAttribute(lambda obj: str(uuid.uuid1()))
    project = factory.SubFactory("tests.factories.ProjectFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class StorageEntryFactory(Factory):
    FACTORY_FOR = get_model("userstorage", "StorageEntry")

    owner = factory.SubFactory("tests.factories.UserFactory")
    key = factory.Sequence(lambda n: "key-{}".format(n))
    value = factory.Sequence(lambda n: "value {}".format(n))


class UserStoryFactory(Factory):
    FACTORY_FOR = get_model("userstories", "UserStory")

    ref = factory.Sequence(lambda n: n)
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    subject = factory.Sequence(lambda n: "User Story {}".format(n))
    description = factory.Sequence(lambda n: "User Story {} description".format(n))
    status = factory.SubFactory("tests.factories.UserStoryStatusFactory")


class UserStoryStatusFactory(Factory):
    FACTORY_FOR = get_model("projects", "UserStoryStatus")

    name = factory.Sequence(lambda n: "User Story status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class TaskFactory(Factory):
    FACTORY_FOR = get_model("tasks", "Task")

    ref = factory.Sequence(lambda n: n)
    owner = factory.SubFactory("tests.factories.UserFactory")
    subject = factory.Sequence(lambda n: "Task {}".format(n))
    user_story = factory.SubFactory("tests.factories.UserStoryFactory")
    status = factory.SubFactory("tests.factories.TaskStatusFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")


class TaskStatusFactory(Factory):
    FACTORY_FOR = get_model("projects", "TaskStatus")

    name = factory.Sequence(lambda n: "Task status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class MilestoneFactory(Factory):
    FACTORY_FOR = get_model("milestones", "Milestone")

    name = factory.Sequence(lambda n: "Milestone {}".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    estimated_start = factory.LazyAttribute(lambda o: date.today())
    estimated_finish = factory.LazyAttribute(lambda o: o.estimated_start + timedelta(days=7))


class IssueFactory(Factory):
    FACTORY_FOR = get_model("issues", "Issue")

    subject = factory.Sequence(lambda n: "Issue {}".format(n))
    description = factory.Sequence(lambda n: "Issue {} description".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    status = factory.SubFactory("tests.factories.IssueStatusFactory")
    severity = factory.SubFactory("tests.factories.SeverityFactory")
    priority = factory.SubFactory("tests.factories.PriorityFactory")
    type = factory.SubFactory("tests.factories.IssueTypeFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")


class TaskFactory(Factory):
    FACTORY_FOR = get_model("tasks", "Task")

    subject = factory.Sequence(lambda n: "Task {}".format(n))
    description = factory.Sequence(lambda n: "Task {} description".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    status = factory.SubFactory("tests.factories.TaskStatusFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")


class WikiPageFactory(Factory):
    FACTORY_FOR = get_model("wiki", "WikiPage")

    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    slug = factory.Sequence(lambda n: "wiki-page-{}".format(n))
    content = factory.Sequence(lambda n: "Wiki Page {} content".format(n))


class IssueStatusFactory(Factory):
    FACTORY_FOR = get_model("projects", "IssueStatus")

    name = factory.Sequence(lambda n: "Issue Status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class TaskStatusFactory(Factory):
    FACTORY_FOR = get_model("projects", "TaskStatus")

    name = factory.Sequence(lambda n: "Issue Status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class SeverityFactory(Factory):
    FACTORY_FOR = get_model("projects", "Severity")

    name = factory.Sequence(lambda n: "Severity {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class PriorityFactory(Factory):
    FACTORY_FOR = get_model("projects", "Priority")

    name = factory.Sequence(lambda n: "Priority {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class IssueTypeFactory(Factory):
    FACTORY_FOR = get_model("projects", "IssueType")

    name = factory.Sequence(lambda n: "Issue Type {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class FanFactory(Factory):
    FACTORY_FOR = get_model("stars", "Fan")

    project = factory.SubFactory("tests.factories.ProjectFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class StarsFactory(Factory):
    FACTORY_FOR = get_model("stars", "Stars")

    project = factory.SubFactory("tests.factories.ProjectFactory")
    count = 0


class VoteFactory(Factory):
    FACTORY_FOR = get_model("votes", "Vote")

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    user = factory.SubFactory("tests.factories.UserFactory")


class VotesFactory(Factory):
    FACTORY_FOR = get_model("votes", "Votes")

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)


class ContentTypeFactory(Factory):
    FACTORY_FOR = get_model("contenttypes", "ContentType")
    FACTORY_DJANGO_GET_OR_CREATE = ("app_label", "model")

    app_label = factory.LazyAttribute(lambda obj: ContentTypeFactory.FACTORY_FOR._meta.app_label)
    model = factory.LazyAttribute(lambda obj: ContentTypeFactory.FACTORY_FOR._meta.model_name)


def create_issue(**kwargs):
    "Create an issue and along with its dependencies."
    owner = kwargs.pop("owner", UserFactory())
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


def create_task(**kwargs):
    "Create a task and along with its dependencies."
    owner = kwargs.pop("owner", UserFactory())
    project = ProjectFactory.create(owner=owner)
    defaults = {
        "project": project,
        "owner": owner,
        "status": TaskStatusFactory.create(project=project),
        "milestone": MilestoneFactory.create(project=project),
        "user_story": UserStoryFactory.create(project=project, owner=owner),
    }
    defaults.update(kwargs)

    return TaskFactory.create(**defaults)


def create_membership(**kwargs):
    "Create a membership along with its dependencies"
    project = kwargs.pop("project", ProjectFactory())
    project.points.add(PointsFactory.create(project=project, value=None))

    defaults = {
        "project": project,
        "user": project.owner,
        "role": RoleFactory.create(project=project)
    }
    defaults.update(kwargs)

    return MembershipFactory.create(**defaults)
