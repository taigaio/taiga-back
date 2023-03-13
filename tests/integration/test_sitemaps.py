import pytest

from django.urls import reverse
from lxml import etree

from taiga.users.models import User

from tests import factories as f
from tests.utils import disconnect_signals, reconnect_signals


pytestmark = pytest.mark.django_db


NAMESPACES = {
    "sitemapindex": "http://www.sitemaps.org/schemas/sitemap/0.9",
}

def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("InitialData", (object,), {})()

    m.project1 = f.ProjectFactory.create(is_private=False,
                                         is_epics_activated=True,
                                         is_backlog_activated=True,
                                         is_kanban_activated=True,
                                         is_issues_activated=True,
                                         is_wiki_activated=True)
    m.project2 = f.ProjectFactory.create(is_private=True,
                                         is_epics_activated=True,
                                         is_backlog_activated=True,
                                         is_kanban_activated=True,
                                         is_issues_activated=True,
                                         is_wiki_activated=True)

    m.epic11 = f.EpicFactory(project=m.project1)
    m.epic21 = f.EpicFactory(project=m.project2)

    m.milestone11 = f.MilestoneFactory(project=m.project1)
    m.milestone21 = f.MilestoneFactory(project=m.project2)

    m.us11 = f.UserStoryFactory(project=m.project1)
    m.us21 = f.UserStoryFactory(project=m.project2)

    m.task11 = f.TaskFactory(project=m.project1)
    m.task21 = f.TaskFactory(project=m.project2)

    m.issue11 = f.IssueFactory(project=m.project1)
    m.issue21 = f.IssueFactory(project=m.project2)

    m.wikipage11 = f.WikiPageFactory(project=m.project1)
    m.wikipage21 = f.WikiPageFactory(project=m.project2)

    return m


def test_sitemaps_index(client):
    url = reverse('front-sitemap-index')

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 11  # ["/generics", "/projects", "/project_backlogs", "/project_kanbans", "/epics",
                            #  "/milestones", "/userstories", "/tasks", "/issues", "/wikipages", "/users"]


def test_sitemap_generics(client, data):
    url = reverse('front-sitemap', kwargs={"section": "generics"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 5  # ["/", "/discover", "/login", "/register", "/forgot-password"]


def test_sitemap_projects(client, data):
    url = reverse('front-sitemap', kwargs={"section": "projects"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_project_backlogs(client, data):
    url = reverse('front-sitemap', kwargs={"section": "project-backlogs"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_project_kanbans(client, data):
    url = reverse('front-sitemap', kwargs={"section": "project-kanbans"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_epics(client, data):
    url = reverse('front-sitemap', kwargs={"section": "epics"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_milestones(client, data):
    url = reverse('front-sitemap', kwargs={"section": "milestones"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_userstories(client, data):
    url = reverse('front-sitemap', kwargs={"section": "userstories"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_tasks(client, data):
    url = reverse('front-sitemap', kwargs={"section": "tasks"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_issues(client, data):
    url = reverse('front-sitemap', kwargs={"section": "issues"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_wikipages(client, data):
    url = reverse('front-sitemap', kwargs={"section": "wikipages"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == 1


def test_sitemap_users(client, data):
    url = reverse('front-sitemap', kwargs={"section": "users"})

    response = client.get(url)
    assert response.status_code == 200, response.data

    tree = etree.fromstring(response.content)
    urls = tree.xpath("//sitemapindex:loc/text()", namespaces=NAMESPACES)
    assert len(urls) == User.objects.filter(is_active=True, is_system=False).count()
