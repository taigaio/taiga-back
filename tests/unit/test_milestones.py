# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from .. import factories as f
from taiga.projects.milestones import services

pytestmark = pytest.mark.django_db(transaction=True)


def test_issues_not_closed():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.IssueStatusFactory.create(project=project,
                                                is_closed=True)
    f.create_issue(project=project, milestone=milestone1,
                   status=closed_status)
    f.create_issue(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_issues_closed():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.IssueStatusFactory.create(project=project,
                                                is_closed=True)
    f.create_issue(project=project, milestone=milestone1,
                   status=closed_status)

    assert services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_issues_but_closed_tasks():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    tasks_closed_status = f.TaskStatusFactory.create(project=project,
                                                     is_closed=True)
    f.create_task(project=project, milestone=milestone1,
                  taskboard_order=1, status=tasks_closed_status)
    f.create_issue(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_issues_but_closed_uss():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    us_closed_status = f.UserStoryStatusFactory.create(project=project,
                                                       is_closed=True)
    f.create_userstory(project=project, milestone=milestone1,
                       status=us_closed_status, is_closed=True)

    f.create_issue(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_closed_issues_but_open_uss():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.IssueStatusFactory.create(project=project,
                                                is_closed=True)
    f.create_issue(project=project, milestone=milestone1,
                   status=closed_status)

    f.create_userstory(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_closed_issues_but_open_tasks():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.IssueStatusFactory.create(project=project,
                                                is_closed=True)
    f.create_issue(project=project, milestone=milestone1,
                   status=closed_status)

    f.create_task(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_tasks_not_closed():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.TaskStatusFactory.create(project=project,
                                               is_closed=True)
    f.create_task(project=project, milestone=milestone1,
                  status=closed_status)
    f.create_task(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_tasks_closed():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.TaskStatusFactory.create(project=project,
                                               is_closed=True)
    f.create_task(project=project, milestone=milestone1,
                  status=closed_status, user_story=None)

    assert services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_tasks_but_closed_issues():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    issue_closed_status = f.IssueStatusFactory.create(project=project,
                                                      is_closed=True)
    f.create_issue(project=project, milestone=milestone1,
                   status=issue_closed_status)
    f.create_task(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_tasks_but_closed_uss():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    us_closed_status = f.UserStoryStatusFactory.create(project=project,
                                                       is_closed=True)
    f.create_userstory(project=project, milestone=milestone1,
                       status=us_closed_status, is_closed=True)

    f.create_task(project=project, milestone=milestone1, user_story=None)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_closed_tasks_but_open_uss():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    closed_status = f.TaskStatusFactory.create(project=project,
                                               is_closed=True)
    f.create_task(project=project, milestone=milestone1,
                  status=closed_status, user_story=None)

    f.create_userstory(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_closed_tasks_but_open_issues():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    closed_status = f.TaskStatusFactory.create(project=project,
                                               is_closed=True)
    f.create_task(project=project, milestone=milestone1,
                  status=closed_status, user_story=None)

    f.create_issue(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_uss_not_closed():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.UserStoryStatusFactory.create(project=project,
                                                    is_closed=True)
    f.create_userstory(project=project, milestone=milestone1,
                       status=closed_status, is_closed=True)
    f.create_userstory(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_uss_closed():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.UserStoryStatusFactory.create(project=project,
                                                    is_closed=True)
    f.create_userstory(project=project, milestone=milestone1,
                       sprint_order=1, status=closed_status,
                       is_closed=True)

    assert services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_uss_but_closed_tasks_and_us():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    us_closed_status = f.UserStoryStatusFactory.create(project=project,
                                                       is_closed=True)
    us = f.create_userstory(project=project, milestone=milestone1,
                            status=us_closed_status, is_closed=True)

    task_closed_status = f.TaskStatusFactory.create(project=project,
                                                    is_closed=True)
    f.create_task(project=project, milestone=milestone1, user_story=us,
                  status=task_closed_status)

    f.create_userstory(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_uss_but_closed_tasks():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.TaskStatusFactory.create(project=project,
                                               is_closed=True)
    f.create_task(project=project, milestone=milestone1,
                  status=closed_status, user_story=None)
    f.create_userstory(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)


def test_stay_open_with_uss_but_closed_issues():
    project = f.ProjectFactory()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)

    closed_status = f.IssueStatusFactory.create(project=project,
                                                is_closed=True)
    f.create_issue(project=project, milestone=milestone1,
                   status=closed_status)
    f.create_userstory(project=project, milestone=milestone1)

    assert not services.calculate_milestone_is_closed(milestone1)
