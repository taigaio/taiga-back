import uuid

import factory
from django.conf import settings

import taiga.domains.models
import taiga.projects.models
import taiga.users.models
import taiga.userstorage.models


class DomainFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.domains.models.Domain
    FACTORY_DJANGO_GET_OR_CREATE = ("domain",)

    name = "Default domain"
    domain = "default"
    scheme = None
    public_register = False


class ProjectTemplateFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.ProjectTemplate

    name = "Template name"
    slug = settings.DEFAULT_PROJECT_TEMPLATE
    default_owner_role = "tester"


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.projects.models.Project

    name = factory.Sequence(lambda n: "Project {}".format(n))
    slug = factory.Sequence(lambda n: "project-{}-slug".format(n))
    description = "Project description"
    owner = factory.SubFactory("tests.factories.UserFactory")
    domain = factory.SubFactory("tests.factories.DomainFactory")
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

    token = factory.LazyAttribute(lambda obj: uuid.uuid1())
    project = factory.SubFactory("tests.factories.ProjectFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class StorageEntryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = taiga.userstorage.models.StorageEntry

    owner = factory.SubFactory("tests.factories.UserFactory")
    key = factory.Sequence(lambda n: "key-{}".format(n))
    value = factory.Sequence(lambda n: "value {}".format(n))
