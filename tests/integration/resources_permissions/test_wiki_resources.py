from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS
from taiga.projects.notifications.services import add_watcher
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.wiki.serializers import WikiPageSerializer, WikiLinkSerializer
from taiga.projects.wiki.models import WikiPage, WikiLink

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals

from unittest import mock

import pytest
pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()

    m.public_project = f.ProjectFactory(is_private=False,
                                        anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                        public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                        owner=m.project_owner)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                          owner=m.project_owner)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner)

    m.public_membership = f.MembershipFactory(project=m.public_project,
                                              user=m.project_member_with_perms,
                                              role__project=m.public_project,
                                              role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.private_membership1 = f.MembershipFactory(project=m.private_project1,
                                                user=m.project_member_with_perms,
                                                role__project=m.private_project1,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project1,
                        user=m.project_member_without_perms,
                        role__project=m.private_project1,
                        role__permissions=[])
    m.private_membership2 = f.MembershipFactory(project=m.private_project2,
                                                user=m.project_member_with_perms,
                                                role__project=m.private_project2,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project2,
                        user=m.project_member_without_perms,
                        role__project=m.private_project2,
                        role__permissions=[])

    f.MembershipFactory(project=m.public_project,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project2,
                        user=m.project_owner,
                        is_owner=True)

    m.public_wiki_page = f.WikiPageFactory(project=m.public_project)
    m.private_wiki_page1 = f.WikiPageFactory(project=m.private_project1)
    m.private_wiki_page2 = f.WikiPageFactory(project=m.private_project2)

    m.public_wiki_link = f.WikiLinkFactory(project=m.public_project)
    m.private_wiki_link1 = f.WikiLinkFactory(project=m.private_project1)
    m.private_wiki_link2 = f.WikiLinkFactory(project=m.private_project2)

    return m


def test_wiki_page_retrieve(client, data):
    public_url = reverse('wiki-detail', kwargs={"pk": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_wiki_page_update(client, data):
    public_url = reverse('wiki-detail', kwargs={"pk": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            wiki_page_data = WikiPageSerializer(data.public_wiki_page).data
            wiki_page_data["content"] = "test"
            wiki_page_data = json.dumps(wiki_page_data)
            results = helper_test_http_method(client, 'put', public_url, wiki_page_data, users)
            assert results == [401, 200, 200, 200, 200]

            wiki_page_data = WikiPageSerializer(data.private_wiki_page1).data
            wiki_page_data["content"] = "test"
            wiki_page_data = json.dumps(wiki_page_data)
            results = helper_test_http_method(client, 'put', private_url1, wiki_page_data, users)
            assert results == [401, 200, 200, 200, 200]

            wiki_page_data = WikiPageSerializer(data.private_wiki_page2).data
            wiki_page_data["content"] = "test"
            wiki_page_data = json.dumps(wiki_page_data)
            results = helper_test_http_method(client, 'put', private_url2, wiki_page_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_wiki_page_delete(client, data):
    public_url = reverse('wiki-detail', kwargs={"pk": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
    ]
    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url1, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url2, None, users)
    assert results == [401, 403, 403, 204]


def test_wiki_page_list(client, data):
    url = reverse('wiki-list')

    response = client.get(url)
    wiki_pages_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_pages_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    wiki_pages_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_pages_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    wiki_pages_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_pages_data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    wiki_pages_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_pages_data) == 3
    assert response.status_code == 200


def test_wiki_page_create(client, data):
    url = reverse('wiki-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    create_data = json.dumps({
        "content": "test",
        "slug": "test",
        "project": data.public_project.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: WikiPage.objects.all().delete())
    assert results == [401, 201, 201, 201, 201]

    create_data = json.dumps({
        "content": "test",
        "slug": "test",
        "project": data.private_project1.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: WikiPage.objects.all().delete())
    assert results == [401, 201, 201, 201, 201]

    create_data = json.dumps({
        "content": "test",
        "slug": "test",
        "project": data.private_project2.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: WikiPage.objects.all().delete())
    assert results == [401, 403, 403, 201, 201]


def test_wiki_page_patch(client, data):
    public_url = reverse('wiki-detail', kwargs={"pk": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-detail', kwargs={"pk": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            patch_data = json.dumps({"content": "test", "version": data.public_wiki_page.version})
            results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
            assert results == [401, 200, 200, 200, 200]

            patch_data = json.dumps({"content": "test", "version": data.private_wiki_page2.version})
            results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
            assert results == [401, 200, 200, 200, 200]

            patch_data = json.dumps({"content": "test", "version": data.private_wiki_page2.version})
            results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_wiki_page_action_render(client, data):
    url = reverse('wiki-render')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({"content": "test", "project_id": data.public_project.pk})
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [200, 200, 200, 200, 200]


def test_wiki_link_retrieve(client, data):
    public_url = reverse('wiki-links-detail', kwargs={"pk": data.public_wiki_link.pk})
    private_url1 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link1.pk})
    private_url2 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_wiki_link_update(client, data):
    public_url = reverse('wiki-links-detail', kwargs={"pk": data.public_wiki_link.pk})
    private_url1 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link1.pk})
    private_url2 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            wiki_link_data = WikiLinkSerializer(data.public_wiki_link).data
            wiki_link_data["title"] = "test"
            wiki_link_data = json.dumps(wiki_link_data)
            results = helper_test_http_method(client, 'put', public_url, wiki_link_data, users)
            assert results == [401, 200, 200, 200, 200]

            wiki_link_data = WikiLinkSerializer(data.private_wiki_link1).data
            wiki_link_data["title"] = "test"
            wiki_link_data = json.dumps(wiki_link_data)
            results = helper_test_http_method(client, 'put', private_url1, wiki_link_data, users)
            assert results == [401, 200, 200, 200, 200]

            wiki_link_data = WikiLinkSerializer(data.private_wiki_link2).data
            wiki_link_data["title"] = "test"
            wiki_link_data = json.dumps(wiki_link_data)
            results = helper_test_http_method(client, 'put', private_url2, wiki_link_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_wiki_link_delete(client, data):
    public_url = reverse('wiki-links-detail', kwargs={"pk": data.public_wiki_link.pk})
    private_url1 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link1.pk})
    private_url2 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
    ]
    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url1, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url2, None, users)
    assert results == [401, 403, 403, 204]


def test_wiki_link_list(client, data):
    url = reverse('wiki-links-list')

    response = client.get(url)
    wiki_links_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_links_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    wiki_links_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_links_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    wiki_links_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_links_data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    wiki_links_data = json.loads(response.content.decode('utf-8'))
    assert len(wiki_links_data) == 3
    assert response.status_code == 200


def test_wiki_link_create(client, data):
    url = reverse('wiki-links-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    create_data = json.dumps({
        "title": "test",
        "href": "test",
        "project": data.public_project.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: WikiLink.objects.all().delete())
    assert results == [401, 201, 201, 201, 201]

    create_data = json.dumps({
        "title": "test",
        "href": "test",
        "project": data.private_project1.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: WikiLink.objects.all().delete())
    assert results == [401, 201, 201, 201, 201]

    create_data = json.dumps({
        "title": "test",
        "href": "test",
        "project": data.private_project2.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: WikiLink.objects.all().delete())
    assert results == [401, 403, 403, 201, 201]


def test_wiki_link_patch(client, data):
    public_url = reverse('wiki-links-detail', kwargs={"pk": data.public_wiki_link.pk})
    private_url1 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link1.pk})
    private_url2 = reverse('wiki-links-detail', kwargs={"pk": data.private_wiki_link2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            patch_data = json.dumps({"title": "test"})
            results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
            assert results == [401, 200, 200, 200, 200]

            patch_data = json.dumps({"title": "test"})
            results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
            assert results == [401, 200, 200, 200, 200]

            patch_data = json.dumps({"title": "test"})
            results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_wikipage_action_watch(client, data):
    public_url = reverse('wiki-watch', kwargs={"pk": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-watch', kwargs={"pk": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-watch', kwargs={"pk": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, "", users)
    assert results == [404, 404, 404, 200, 200]


def test_wikipage_action_unwatch(client, data):
    public_url = reverse('wiki-unwatch', kwargs={"pk": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-unwatch', kwargs={"pk": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-unwatch', kwargs={"pk": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, "", users)
    assert results == [404, 404, 404, 200, 200]


def test_wikipage_watchers_list(client, data):
    public_url = reverse('wiki-watchers-list', kwargs={"resource_id": data.public_wiki_page.pk})
    private_url1 = reverse('wiki-watchers-list', kwargs={"resource_id": data.private_wiki_page1.pk})
    private_url2 = reverse('wiki-watchers-list', kwargs={"resource_id": data.private_wiki_page2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_wikipage_watchers_retrieve(client, data):
    add_watcher(data.public_wiki_page, data.project_owner)
    public_url = reverse('wiki-watchers-detail', kwargs={"resource_id": data.public_wiki_page.pk,
                                                        "pk": data.project_owner.pk})
    add_watcher(data.private_wiki_page1, data.project_owner)
    private_url1 = reverse('wiki-watchers-detail', kwargs={"resource_id": data.private_wiki_page1.pk,
                                                          "pk": data.project_owner.pk})
    add_watcher(data.private_wiki_page2, data.project_owner)
    private_url2 = reverse('wiki-watchers-detail', kwargs={"resource_id": data.private_wiki_page2.pk,
                                                          "pk": data.project_owner.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]
