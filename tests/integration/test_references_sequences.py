# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.urls import reverse

from .. import factories


@pytest.fixture
def seq():
    from taiga.projects.references import sequences as seq
    return seq


@pytest.fixture
def refmodels():
    from taiga.projects.references import models
    return models


@pytest.mark.django_db
def test_sequences(seq):
    seqname = "foo"
    assert not seq.exists(seqname)

    # Create and check values
    seq.create(seqname)
    assert seq.exists(seqname)
    assert seq.next_value(seqname) == 1
    assert seq.next_value(seqname) == 2

    # Delete sequence
    seq.delete(seqname)
    assert not seq.exists(seqname)

    # Create new seq with same name
    # after previously deleted it
    seq.create(seqname)
    assert seq.next_value(seqname) == 1

    # Alter sequence
    seq.alter(seqname, 4)
    assert seq.next_value(seqname) == 5

    # Delete after alter
    seq.delete(seqname)
    assert not seq.exists(seqname)


@pytest.mark.django_db
def test_unique_reference_per_project(seq, refmodels):
    refmodels.Reference.objects.all().delete()

    project = factories.ProjectFactory.create()
    seqname = refmodels.make_sequence_name(project)

    assert seqname == "references_project{0}".format(project.id)
    assert seq.exists(seqname)

    assert refmodels.make_unique_reference_id(project, create=True) == 1
    assert refmodels.make_unique_reference_id(project, create=True) == 2

    project.delete()
    assert not seq.exists(seqname)


@pytest.mark.django_db
def test_regenerate_us_reference_on_project_change(seq, refmodels):
    refmodels.Reference.objects.all().delete()

    project1 = factories.ProjectFactory.create()
    seqname1 = refmodels.make_sequence_name(project1)
    project2 = factories.ProjectFactory.create()
    seqname2 = refmodels.make_sequence_name(project2)

    seq.alter(seqname1, 100)
    seq.alter(seqname2, 200)

    user_story = factories.UserStoryFactory.create(project=project1)
    assert user_story.ref == 101

    user_story.subject = "other"
    user_story.save()
    assert user_story.ref == 101

    user_story.project = project2
    user_story.save()

    assert user_story.ref == 201

@pytest.mark.django_db
def test_regenerate_task_reference_on_project_change(seq, refmodels):
    refmodels.Reference.objects.all().delete()

    project1 = factories.ProjectFactory.create()
    seqname1 = refmodels.make_sequence_name(project1)
    project2 = factories.ProjectFactory.create()
    seqname2 = refmodels.make_sequence_name(project2)

    seq.alter(seqname1, 100)
    seq.alter(seqname2, 200)

    task = factories.TaskFactory.create(project=project1)
    assert task.ref == 101

    task.subject = "other"
    task.save()
    assert task.ref == 101

    task.project = project2
    task.save()

    assert task.ref == 201

@pytest.mark.django_db
def test_regenerate_issue_reference_on_project_change(seq, refmodels):
    refmodels.Reference.objects.all().delete()

    project1 = factories.ProjectFactory.create()
    seqname1 = refmodels.make_sequence_name(project1)
    project2 = factories.ProjectFactory.create()
    seqname2 = refmodels.make_sequence_name(project2)

    seq.alter(seqname1, 100)
    seq.alter(seqname2, 200)

    issue = factories.IssueFactory.create(project=project1)
    assert issue.ref == 101

    issue.subject = "other"
    issue.save()
    assert issue.ref == 101

    issue.project = project2
    issue.save()

    assert issue.ref == 201


@pytest.mark.django_db
def test_params_validation_in_api_request(client, refmodels):
    refmodels.Reference.objects.all().delete()

    user = factories.UserFactory.create()
    project = factories.ProjectFactory.create(owner=user)
    seqname1 = refmodels.make_sequence_name(project)
    role = factories.RoleFactory.create(project=project)
    factories.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)

    milestone = factories.MilestoneFactory.create(project=project)
    us = factories.UserStoryFactory.create(project=project)
    task = factories.TaskFactory.create(project=project)
    issue = factories.IssueFactory.create(project=project)
    wiki_page = factories.WikiPageFactory.create(project=project)

    client.login(user)

    url = reverse("resolver-list")
    response = client.json.get(url)
    assert response.status_code == 400
    response = client.json.get("{}?project={}".format(url, project.slug))
    assert response.status_code == 200
    response = client.json.get("{}?project={}&ref={}".format(url, project.slug, us.ref))
    assert response.status_code == 200
    response = client.json.get("{}?project={}&ref={}&us={}".format(url, project.slug, us.ref, us.ref))
    assert response.status_code == 400
    response = client.json.get("{}?project={}&ref={}&task={}".format(url, project.slug, us.ref, task.ref))
    assert response.status_code == 400
    response = client.json.get("{}?project={}&ref={}&issue={}".format(url, project.slug, us.ref, issue.ref))
    assert response.status_code == 400
    response = client.json.get("{}?project={}&us={}&task={}".format(url, project.slug, us.ref, task.ref))
    assert response.status_code == 200
    response = client.json.get("{}?project={}&ref={}&milestone={}".format(url, project.slug, us.ref,
                                                                          milestone.slug))
    assert response.status_code == 200


@pytest.mark.django_db
def test_by_ref_calls_in_api_request(client, refmodels):
    refmodels.Reference.objects.all().delete()

    user = factories.UserFactory.create()
    project = factories.ProjectFactory.create(owner=user)
    seqname1 = refmodels.make_sequence_name(project)
    role = factories.RoleFactory.create(project=project)
    factories.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)

    epic = factories.EpicFactory.create(project=project)
    milestone = factories.MilestoneFactory.create(project=project)
    us = factories.UserStoryFactory.create(project=project)
    task = factories.TaskFactory.create(project=project)
    issue = factories.IssueFactory.create(project=project)
    wiki_page = factories.WikiPageFactory.create(project=project)

    client.login(user)

    url = reverse("resolver-list")
    response = client.json.get("{}?project={}&ref={}".format(url, project.slug, epic.ref))
    assert response.status_code == 200
    assert response.data["epic"] == epic.id

    response = client.json.get("{}?project={}&ref={}".format(url, project.slug, us.ref))
    assert response.status_code == 200
    assert response.data["us"] == us.id

    response = client.json.get("{}?project={}&ref={}".format(url, project.slug, task.ref))
    assert response.status_code == 200
    assert response.data["task"] == task.id

    response = client.json.get("{}?project={}&ref={}".format(url, project.slug, issue.ref))
    assert response.status_code == 200
    assert response.data["issue"] == issue.id

    response = client.json.get("{}?project={}&ref={}".format(url, project.slug, wiki_page.slug))
    assert response.status_code == 200
    assert response.data["wikipage"] == wiki_page.id
