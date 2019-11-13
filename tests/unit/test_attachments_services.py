import pytest

from taiga.projects.attachments import services

from .. import factories as f


@pytest.mark.django_db(transaction=True)
def test_get_attachment_by_id(django_assert_num_queries):
    att, other_att = f.IssueAttachmentFactory(), f.IssueAttachmentFactory()
    assert att.content_object.project_id != other_att.content_object.project_id

    # Attachment not exist
    with django_assert_num_queries(1):
        assert services.get_attachment_by_id(other_att.content_object.project_id, 99999) is None

    # Attachment does not belong to an object of the project
    with django_assert_num_queries(2):
        assert services.get_attachment_by_id(other_att.content_object.project_id, att.id) is None

    # Attachment do belongs to the project
    with django_assert_num_queries(2):
        assert services.get_attachment_by_id(att.content_object.project_id, att.id) == att


@pytest.mark.parametrize("url, expected", [
    ("http://media.example.com/a/file.png", "http://media.example.com/a/file.png"),
    ("http://media.example.com/a/file.png?token=x", "http://media.example.com/a/file.png?token=x"),
    ("/a/file.png", None),
    ("http://www.example.com/logo.png", None),
])
def test_url_is_an_attachment(url, expected):
    assert services.url_is_an_attachment(url, base="http://media.example.com/a/") == expected
