# -*- coding: utf-8 -*-

from unittest import mock
from types import SimpleNamespace

import pytest

from taiga.importers.github.importer import (
    GithubClient,
    GithubImporter,
    extract_github_inline_image_urls,
)


def test_extract_github_inline_image_urls():
    attachment_url = "https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111"
    markdown = "![image]({}) ![same]({})".format(attachment_url, attachment_url)

    assert extract_github_inline_image_urls(markdown) == [attachment_url]


@pytest.mark.parametrize("markdown", [
    "![image](https://example.com/image.png)",
    "[issue](https://github.com/org/repo/issues/1)",
    "<img src=\"https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111\">",
    "![image](https://github.com/user-attachments/assets/not-a-uuid)",
])
def test_extract_github_inline_image_urls_ignores_unsupported_markdown(markdown):
    assert extract_github_inline_image_urls(markdown) == []


@mock.patch("taiga.importers.github.importer.requests.post")
def test_render_markdown_sends_context_and_authorization(post):
    post.return_value = mock.Mock(status_code=200, text="<img src=\"signed-url\">")
    client = GithubClient("oauth-token")

    rendered = client.render_markdown(
        "![image](https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111)",
        "owner/repository",
    )

    assert rendered == "<img src=\"signed-url\">"
    post.assert_called_once_with(
        "https://api.github.com/markdown",
        json={
            "text": "![image](https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111)",
            "mode": "gfm",
            "context": "owner/repository",
        },
        headers={
            "Accept": "text/html",
            "Content-Type": "application/json",
            "X-GitHub-Media-Type": "github.v3",
            "Authorization": "token oauth-token",
        },
    )


@mock.patch("taiga.importers.github.importer.requests.get")
def test_download_does_not_send_github_token(get):
    get.return_value = mock.Mock(
        status_code=200,
        content=b"image-bytes",
        headers={"Content-Type": "image/png"},
    )
    client = GithubClient("oauth-token")

    content, headers = client.download("https://private-user-images.githubusercontent.com/signed")

    assert content == b"image-bytes"
    assert headers["Content-Type"] == "image/png"
    get.assert_called_once_with("https://private-user-images.githubusercontent.com/signed")


@pytest.mark.parametrize("method", ["render_markdown", "download"])
def test_github_client_raises_for_unavailable_resource(method):
    with mock.patch("taiga.importers.github.importer.requests.post") as post, \
            mock.patch("taiga.importers.github.importer.requests.get") as get:
        post.return_value = mock.Mock(status_code=500, text="error")
        get.return_value = mock.Mock(status_code=404, text="error")
        client = GithubClient("oauth-token")

        with pytest.raises(Exception):
            if method == "render_markdown":
                client.render_markdown("![image](url)", "owner/repository")
            else:
                client.download("https://private-user-images.githubusercontent.com/signed")


@pytest.mark.parametrize("obj_class", [
    type("UserStory", (), {}),
    type("Issue", (), {}),
])
@mock.patch("taiga.importers.github.importer.ContentType")
@mock.patch("taiga.importers.github.importer.Attachment")
def test_import_inline_image_rewrites_markdown_and_creates_attachment(
    attachment_class, content_type_class, obj_class
):
    github_url = "https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111"
    signed_url = "https://private-user-images.githubusercontent.com/mock/image.png?jwt=mock-token"
    markdown = "![image]({}) ![duplicate]({})".format(github_url, github_url)
    attached_file = SimpleNamespace(url="/media/attachments/screenshot.png", save=mock.Mock())
    attachment = SimpleNamespace(
        id=42,
        content_type=SimpleNamespace(model="issue"),
        attached_file=attached_file,
    )
    attachment_class.return_value = attachment
    content_type_class.objects.get_for_model.return_value = attachment.content_type

    client = mock.Mock()
    client.render_markdown.return_value = '<p><img src="{}" alt="image"></p>'.format(signed_url)
    client.download.return_value = (
        b"png-bytes",
        {
            "Content-Type": "image/png",
            "Content-Disposition": "inline; filename=screenshot.png",
        },
    )
    importer = GithubImporter.__new__(GithubImporter)
    importer._client = client
    obj = obj_class()
    obj.id = 7
    obj.owner = SimpleNamespace(id=8)
    obj.project = SimpleNamespace(id=9)

    result = importer._import_inline_images(
        markdown=markdown,
        obj=obj,
        repository_full_name="owner/repository",
        created_date="2026-09-07T10:00:00Z",
    )

    expected_url = "/media/attachments/screenshot.png#_taiga-refresh=issue:42"
    assert result == "![image]({0}) ![duplicate]({0})".format(expected_url)
    client.render_markdown.assert_called_once_with(
        "![image]({})".format(github_url),
        "owner/repository",
    )
    client.download.assert_called_once_with(signed_url)
    attachment_class.assert_called_once_with(
        owner=obj.owner,
        project=obj.project,
        content_type=attachment.content_type,
        object_id=obj.id,
        name="screenshot.png",
        size=len(b"png-bytes"),
        created_date="2026-09-07T10:00:00Z",
        is_deprecated=False,
    )
    attached_file.save.assert_called_once()


@mock.patch("taiga.importers.github.importer.logger.warning")
def test_import_inline_images_keeps_failed_image_and_imports_next_image(warning):
    first_url = "https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111"
    second_url = "https://github.com/user-attachments/assets/22222222-2222-2222-2222-222222222222"
    signed_url = "https://private-user-images.githubusercontent.com/mock/second.png?jwt=mock-token"
    client = mock.Mock()
    client.render_markdown.side_effect = [
        RuntimeError("render failed"),
        '<img src="{}">'.format(signed_url),
    ]
    client.download.return_value = b"bytes", {"Content-Type": "image/png"}

    attached_file = SimpleNamespace(url="/media/attachments/second.png", save=mock.Mock())
    attachment = SimpleNamespace(
        id=42,
        content_type=SimpleNamespace(model="issue"),
        attached_file=attached_file,
    )
    importer = GithubImporter.__new__(GithubImporter)
    importer._client = client
    obj = SimpleNamespace(
        id=7,
        owner=SimpleNamespace(id=8),
        project=SimpleNamespace(id=9),
    )

    with mock.patch("taiga.importers.github.importer.ContentType") as content_type_class, \
            mock.patch("taiga.importers.github.importer.Attachment", return_value=attachment):
        content_type_class.objects.get_for_model.return_value = attachment.content_type
        result = importer._import_inline_images(
            markdown="![first]({}) ![second]({})".format(first_url, second_url),
            obj=obj,
            repository_full_name="owner/repository",
            created_date="2026-09-07T10:00:00Z",
        )

    assert first_url in result
    assert "/media/attachments/second.png#_taiga-refresh=issue:42" in result
    assert client.render_markdown.call_count == 2
    warning.assert_called_once()
