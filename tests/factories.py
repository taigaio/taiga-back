import uuid

import factory
from django.conf import settings

import taiga.projects.models
import taiga.projects.userstories.models
import taiga.projects.issues.models
import taiga.projects.milestones.models
import taiga.users.models
import taiga.userstorage.models


class ProjectTemplateFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.ProjectTemplate
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


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.Project

    name = factory.Sequence(lambda n: "Project {}".format(n))
    slug = factory.Sequence(lambda n: "project-{}-slug".format(n))
    description = "Project description"
    owner = factory.SubFactory("tests.factories.UserFactory")
    creation_template = factory.SubFactory("tests.factories.ProjectTemplateFactory")


class RoleFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.users.models.Role

    name = "Tester"
    project = factory.SubFactory("tests.factories.ProjectFactory")


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.users.models.User

    username = factory.Sequence(lambda n: "user{}".format(n))
    email = factory.LazyAttribute(lambda obj: '%s@email.com' % obj.username)
    password = factory.PostGeneration(lambda obj, *args, **kwargs: obj.set_password(obj.username))


class MembershipFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.Membership

    token = factory.LazyAttribute(lambda obj: str(uuid.uuid1()))
    project = factory.SubFactory("tests.factories.ProjectFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class StorageEntryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.userstorage.models.StorageEntry

    owner = factory.SubFactory("tests.factories.UserFactory")
    key = factory.Sequence(lambda n: "key-{}".format(n))
    value = factory.Sequence(lambda n: "value {}".format(n))


class UserStoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.userstories.models.UserStory

    ref = factory.Sequence(lambda n: n)
    project = factory.SubFactory("tests.factories.ProjectFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    subject = factory.Sequence(lambda n: "User Story {}".format(n))


class MilestoneFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.milestones.models.Milestone

    name = factory.Sequence(lambda n: "Milestone {}".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")


class IssueFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.issues.models.Issue

    subject = factory.Sequence(lambda n: "Issue {}".format(n))
    owner = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    status = factory.SubFactory("tests.factories.IssueStatusFactory")
    severity = factory.SubFactory("tests.factories.SeverityFactory")
    priority = factory.SubFactory("tests.factories.PriorityFactory")
    type = factory.SubFactory("tests.factories.IssueTypeFactory")
    milestone = factory.SubFactory("tests.factories.MilestoneFactory")


class IssueStatusFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.IssueStatus

    name = factory.Sequence(lambda n: "Issue Status {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class SeverityFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.Severity

    name = factory.Sequence(lambda n: "Severity {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class PriorityFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.Priority

    name = factory.Sequence(lambda n: "Priority {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")


class IssueTypeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.IssueType

    name = factory.Sequence(lambda n: "Issue Type {}".format(n))
    project = factory.SubFactory("tests.factories.ProjectFactory")
