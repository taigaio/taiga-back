# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from taiga.projects.userstories.models import UserStory
from taiga.projects.issues.models import Issue
from taiga.base import neighbors as n

from .. import factories as f
from ..utils import disconnect_signals, reconnect_signals


def setup_module():
    disconnect_signals()


def teardown_module():
    reconnect_signals()


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

    def test_results_set_repeat_id(self):
        project = f.ProjectFactory.create()

        us1 = f.UserStoryFactory.create(project=project)
        f.RolePointsFactory.create(user_story=us1)
        f.RolePointsFactory.create(user_story=us1)

        neighbors = n.get_neighbors(us1, results_set=UserStory.objects.get_queryset().filter(role_points__isnull=False))

        assert neighbors.right == us1

    def test_results_set_left_repeat_id(self):
        project = f.ProjectFactory.create()

        us1 = f.UserStoryFactory.create(project=project)
        f.RolePointsFactory.create(user_story=us1)
        f.RolePointsFactory.create(user_story=us1)

        us2 = f.UserStoryFactory.create(project=project)
        f.RolePointsFactory.create(user_story=us2)

        neighbors = n.get_neighbors(us2, results_set=UserStory.objects.get_queryset().filter(role_points__isnull=False))

        assert neighbors.left == us1

    def test_filtered_by_tags(self):
        tag_names = ["test"]
        project = f.ProjectFactory.create()

        f.UserStoryFactory.create(project=project)
        us1 = f.UserStoryFactory.create(project=project, tags=tag_names)
        us2 = f.UserStoryFactory.create(project=project, tags=tag_names)

        test_user_stories = UserStory.objects.get_queryset().filter(tags__contains=tag_names)

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

        assert neighbors.left == issue3
        assert neighbors.right == issue1

    def test_empty_related_queryset(self):
        project = f.ProjectFactory.create()

        issue1 = f.IssueFactory.create(project=project)
        issue2 = f.IssueFactory.create(project=project)
        issue3 = f.IssueFactory.create(project=project)

        neighbors = n.get_neighbors(issue2, Issue.objects.none())

        assert neighbors.left == issue3
        assert neighbors.right == issue1

    def test_ordering_by_severity(self):
        project = f.ProjectFactory.create()
        severity1 = f.SeverityFactory.create(project=project, order=1)
        severity2 = f.SeverityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, severity=severity2)
        issue2 = f.IssueFactory.create(project=project, severity=severity1)
        issue3 = f.IssueFactory.create(project=project, severity=severity1)

        issues = Issue.objects.filter(project=project).order_by("severity", "-id")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue3_neighbors.left is None
        assert issue3_neighbors.right == issue2
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right == issue1

    def test_ordering_by_severity_desc(self):
        project = f.ProjectFactory.create()
        severity1 = f.SeverityFactory.create(project=project, order=1)
        severity2 = f.SeverityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, severity=severity2)
        issue2 = f.IssueFactory.create(project=project, severity=severity1)
        issue3 = f.IssueFactory.create(project=project, severity=severity1)

        issues = Issue.objects.filter(project=project).order_by("-severity", "-id")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue3
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right is None

    def test_ordering_by_status(self):
        project = f.ProjectFactory.create()
        status1 = f.IssueStatusFactory.create(project=project, order=1)
        status2 = f.IssueStatusFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, status=status2)
        issue2 = f.IssueFactory.create(project=project, status=status1)
        issue3 = f.IssueFactory.create(project=project, status=status1)

        issues = Issue.objects.filter(project=project).order_by("status", "-id")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue3_neighbors.left is None
        assert issue3_neighbors.right == issue2
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right == issue1

    def test_ordering_by_status_desc(self):
        project = f.ProjectFactory.create()
        status1 = f.IssueStatusFactory.create(project=project, order=1)
        status2 = f.IssueStatusFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, status=status2)
        issue2 = f.IssueFactory.create(project=project, status=status1)
        issue3 = f.IssueFactory.create(project=project, status=status1)

        issues = Issue.objects.filter(project=project).order_by("-status", "-id")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue3
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right is None

    def test_ordering_by_priority(self):
        project = f.ProjectFactory.create()
        priority1 = f.PriorityFactory.create(project=project, order=1)
        priority2 = f.PriorityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, priority=priority2)
        issue2 = f.IssueFactory.create(project=project, priority=priority1)
        issue3 = f.IssueFactory.create(project=project, priority=priority1)

        issues = Issue.objects.filter(project=project).order_by("priority", "-id")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue3_neighbors.left is None
        assert issue3_neighbors.right == issue2
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right == issue1

    def test_ordering_by_priority_desc(self):
        project = f.ProjectFactory.create()
        priority1 = f.PriorityFactory.create(project=project, order=1)
        priority2 = f.PriorityFactory.create(project=project, order=2)

        issue1 = f.IssueFactory.create(project=project, priority=priority2)
        issue2 = f.IssueFactory.create(project=project, priority=priority1)
        issue3 = f.IssueFactory.create(project=project, priority=priority1)

        issues = Issue.objects.filter(project=project).order_by("-priority", "-id")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue3
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right is None

    def test_ordering_by_owner(self):
        project = f.ProjectFactory.create()
        owner1 = f.UserFactory.create(full_name="Chuck Norris")
        owner2 = f.UserFactory.create(full_name="George Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, owner=owner2)
        issue2 = f.IssueFactory.create(project=project, owner=owner1)
        issue3 = f.IssueFactory.create(project=project, owner=owner1)

        issues = Issue.objects.filter(project=project).order_by("owner__full_name", "-id")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue3_neighbors.left is None
        assert issue3_neighbors.right == issue2
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right == issue1

    def test_ordering_by_owner_desc(self):
        project = f.ProjectFactory.create()
        owner1 = f.UserFactory.create(full_name="Chuck Norris")
        owner2 = f.UserFactory.create(full_name="George Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, owner=owner2)
        issue2 = f.IssueFactory.create(project=project, owner=owner1)
        issue3 = f.IssueFactory.create(project=project, owner=owner1)

        issues = Issue.objects.filter(project=project).order_by("-owner__full_name", "-id")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue3
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right is None

    def test_ordering_by_assigned_to(self):
        project = f.ProjectFactory.create()
        assigned_to1 = f.UserFactory.create(full_name="Chuck Norris")
        assigned_to2 = f.UserFactory.create(full_name="George Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, assigned_to=assigned_to2)
        issue2 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)
        issue3 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)

        issues = Issue.objects.filter(project=project).order_by("assigned_to__full_name", "-id")

        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)
        issue3_neighbors = n.get_neighbors(issue3, results_set=issues)

        assert issue3_neighbors.left is None
        assert issue3_neighbors.right == issue2
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right == issue1

    def test_ordering_by_assigned_to_desc(self):
        project = f.ProjectFactory.create()
        assigned_to1 = f.UserFactory.create(full_name="Chuck Norris")
        assigned_to2 = f.UserFactory.create(full_name="George Of The Jungle")

        issue1 = f.IssueFactory.create(project=project, assigned_to=assigned_to2)
        issue2 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)
        issue3 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)

        issues = Issue.objects.filter(project=project).order_by("-assigned_to__full_name", "-id")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left is None
        assert issue1_neighbors.right == issue3
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right is None

    def test_ordering_by_assigned_to_desc_with_none_values(self):
        project = f.ProjectFactory.create()

        issue1 = f.IssueFactory.create(project=project, assigned_to=None)
        issue2 = f.IssueFactory.create(project=project, assigned_to=None)
        issue3 = f.IssueFactory.create(project=project, assigned_to=None)

        issues = Issue.objects.filter(project=project).order_by("-assigned_to__full_name", "-id")
        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left == issue2
        assert issue1_neighbors.right is None
        assert issue2_neighbors.left == issue3
        assert issue2_neighbors.right == issue1

    def test_ordering_by_assigned_to_desc_with_none_and_normal_values(self):
        project = f.ProjectFactory.create()
        assigned_to1 = f.UserFactory.create(full_name="Chuck Norris")
        issue1 = f.IssueFactory.create(project=project, assigned_to=None)
        issue2 = f.IssueFactory.create(project=project, assigned_to=assigned_to1)
        issue3 = f.IssueFactory.create(project=project, assigned_to=None)

        issues = Issue.objects.filter(project=project).order_by("-assigned_to__full_name", "-id")

        issue1_neighbors = n.get_neighbors(issue1, results_set=issues)
        issue2_neighbors = n.get_neighbors(issue2, results_set=issues)

        assert issue1_neighbors.left == issue3
        assert issue1_neighbors.right == issue2
        assert issue2_neighbors.left == issue1
        assert issue2_neighbors.right is None
