from functools import partial
from unittest import mock

import pytest

from taiga.projects.userstories.models import UserStory
from taiga.projects.issues.models import Issue
from taiga.base.utils.db import filter_by_tags
from taiga.base import neighbors as n

from .. import factories as f
from ..utils import disconnect_signals


def setup_module():
    disconnect_signals()


class TestGetAttribute:
    def test_no_attribute(self, object):
        object.first_name = "name"
        with pytest.raises(AttributeError):
            n.get_attribute(object, "name")

        with pytest.raises(AttributeError):
            n.get_attribute(object, "first_name__last_name")

    def test_one_level(self, object):
        object.name = "name"
        assert n.get_attribute(object, "name") == object.name

    def test_two_levels(self, object):
        object.name = object
        object.name.first_name = "first name"
        assert n.get_attribute(object, "name__first_name") == object.name.first_name

    def test_three_levels(self, object):
        object.info = object
        object.info.name = object
        object.info.name.first_name = "first name"
        assert n.get_attribute(object, "info__name__first_name") == object.info.name.first_name


def test_transform_field_into_lookup():
    transform = partial(n.transform_field_into_lookup, value="chuck", operator="__lt",
                        operator_if_desc="__gt")

    assert transform(name="name") == {"name__lt": "chuck"}
    assert transform(name="-name") == {"name__gt": "chuck"}


def test_disjunction_filters():
    filters = [{"age__lt": 21, "name__eq": "chuck"}]
    result_str = str(n.disjunction_filters(filters))

    assert result_str.startswith("(OR: ")
    assert "('age__lt', 21)" in result_str
    assert "('name__eq', 'chuck')" in result_str


@pytest.mark.django_db
class TestUserStories:
    def test_no_filters(self):
        project = f.ProjectFactory.create()

        us1 = f.UserStoryFactory.create(project=project)
        us2 = f.UserStoryFactory.create(project=project)
        us3 = f.UserStoryFactory.create(project=project)

        neighbors = n.get_neighbors(us2)

        assert neighbors.left == us1
        assert neighbors.right == us3

    def test_filtered_by_tags(self):
        tags = ["test"]
        project = f.ProjectFactory.create()

        f.UserStoryFactory.create(project=project)
        us1 = f.UserStoryFactory.create(project=project, tags=tags)
        us2 = f.UserStoryFactory.create(project=project, tags=tags)

        test_user_stories = filter_by_tags(tags, queryset=UserStory.objects.get_queryset())

        neighbors = n.get_neighbors(us1, results_set=test_user_stories)

        assert neighbors.left is None
        assert neighbors.right == us2

    def test_filtered_by_milestone(self):
        project = f.ProjectFactory.create()
        milestone = f.MilestoneFactory.create(project=project)

        f.UserStoryFactory.create(project=project)
        us1 = f.UserStoryFactory.create(project=project, milestone=milestone)
        us2 = f.UserStoryFactory.create(project=project, milestone=milestone)

        milestone_user_stories = UserStory.objects.filter(milestone=milestone)

        neighbors = n.get_neighbors(us1, results_set=milestone_user_stories)

        assert neighbors.left is None
        assert neighbors.right == us2


@pytest.mark.django_db
class TestIssues:
    def test_no_filters(self):
        project = f.ProjectFactory.create()

        issue1 = f.IssueFactory.create(project=project)
        issue2 = f.IssueFactory.create(project=project)
        issue3 = f.IssueFactory.create(project=project)

        neighbors = n.get_neighbors(issue2)

        assert neighbors.left == issue1
        assert neighbors.right == issue3

    def test_ordering_by_severity(self):
        project = f.ProjectFactory.create()
        severity1 = f.SeverityFactory.create(project=project, order=1)
        severity2 = f.SeverityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, severity=severity2)
        issue2 = f.IssueFactory.create(project=project, severity=severity1)
        issue3 = f.IssueFactory.create(project=project, severity=severity1)

        issues = Issue.objects.filter(project=project).order_by("severity")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue2_neighbors.left is None
        assert issue2_neighbors.right == issue3
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right == issue1

    def test_ordering_by_severity_desc(self):
        project = f.ProjectFactory.create()
        severity1 = f.SeverityFactory.create(project=project, order=1)
        severity2 = f.SeverityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, severity=severity2)
        issue2 = f.IssueFactory.create(project=project, severity=severity1)
        issue3 = f.IssueFactory.create(project=project, severity=severity1)

        issues = Issue.objects.filter(project=project).order_by("-severity")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue2
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right is None

    def test_ordering_by_status(self):
        project = f.ProjectFactory.create()
        status1 = f.IssueStatusFactory.create(project=project, order=1)
        status2 = f.IssueStatusFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, status=status2)
        issue2 = f.IssueFactory.create(project=project, status=status1)
        issue3 = f.IssueFactory.create(project=project, status=status1)

        issues = Issue.objects.filter(project=project).order_by("status")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue2_neighbors.left is None
        assert issue2_neighbors.right == issue3
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right == issue1

    def test_ordering_by_status_desc(self):
        project = f.ProjectFactory.create()
        status1 = f.IssueStatusFactory.create(project=project, order=1)
        status2 = f.IssueStatusFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, status=status2)
        issue2 = f.IssueFactory.create(project=project, status=status1)
        issue3 = f.IssueFactory.create(project=project, status=status1)

        issues = Issue.objects.filter(project=project).order_by("-status")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue2
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right is None

    def test_ordering_by_priority(self):
        project = f.ProjectFactory.create()
        priority1 = f.PriorityFactory.create(project=project, order=1)
        priority2 = f.PriorityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, priority=priority2)
        issue2 = f.IssueFactory.create(project=project, priority=priority1)
        issue3 = f.IssueFactory.create(project=project, priority=priority1)

        issues = Issue.objects.filter(project=project).order_by("priority")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue2_neighbors.left is None
        assert issue2_neighbors.right == issue3
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right == issue1

    def test_ordering_by_priority_desc(self):
        project = f.ProjectFactory.create()
        priority1 = f.PriorityFactory.create(project=project, order=1)
        priority2 = f.PriorityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, priority=priority2)
        issue2 = f.IssueFactory.create(project=project, priority=priority1)
        issue3 = f.IssueFactory.create(project=project, priority=priority1)

        issues = Issue.objects.filter(project=project).order_by("-priority")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue2
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right is None

    def test_ordering_by_owner(self):
        project = f.ProjectFactory.create()
        owner1 = f.UserFactory.create(first_name="Chuck", last_name="Norris")
        owner2 = f.UserFactory.create(first_name="George", last_name="Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, owner=owner2)
        issue2 = f.IssueFactory.create(project=project, owner=owner1)
        issue3 = f.IssueFactory.create(project=project, owner=owner1)

        issues = Issue.objects.filter(project=project).order_by("owner__first_name")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue2_neighbors.left is None
        assert issue2_neighbors.right == issue3
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right == issue1

    def test_ordering_by_owner_desc(self):
        project = f.ProjectFactory.create()
        owner1 = f.UserFactory.create(first_name="Chuck", last_name="Norris")
        owner2 = f.UserFactory.create(first_name="George", last_name="Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, owner=owner2)
        issue2 = f.IssueFactory.create(project=project, owner=owner1)
        issue3 = f.IssueFactory.create(project=project, owner=owner1)

        issues = Issue.objects.filter(project=project).order_by("-owner__first_name")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue2
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right is None

    def test_ordering_by_assigned_to(self):
        project = f.ProjectFactory.create()
        assigned_to1 = f.UserFactory.create(first_name="Chuck", last_name="Norris")
        assigned_to2 = f.UserFactory.create(first_name="George", last_name="Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, assigned_to=assigned_to2)
        issue2 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)
        issue3 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)

        issues = Issue.objects.filter(project=project).order_by("assigned_to__first_name")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue2_neighbors.left is None
        assert issue2_neighbors.right == issue3
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right == issue1

    def test_ordering_by_assigned_to_desc(self):
        project = f.ProjectFactory.create()
        assigned_to1 = f.UserFactory.create(first_name="Chuck", last_name="Norris")
        assigned_to2 = f.UserFactory.create(first_name="George", last_name="Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, assigned_to=assigned_to2)
        issue2 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)
        issue3 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)

        issues = Issue.objects.filter(project=project).order_by("-assigned_to__first_name")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue2
        assert issue3_neighbors.left == issue2
        assert issue3_neighbors.right is None
