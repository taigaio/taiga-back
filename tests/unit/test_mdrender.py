# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from unittest.mock import patch, MagicMock

from taiga.mdrender.extensions import emojify
from taiga.mdrender.extensions import refresh_attachment
from taiga.mdrender.service import render, cache_by_sha, get_diff_of_htmls, render_and_extract
from taiga.projects.attachments.services import REFRESH_PARAM

import time

dummy_project = MagicMock()
dummy_project.id = 1
dummy_project.slug = "test"


dummy_object = MagicMock()
del dummy_object.slug
dummy_object.project = dummy_project


def test_proccessor_valid_emoji():
    result = emojify.EmojifyPreprocessor().run(["**:smile:**"])
    assert result == ["**![smile](http://localhost:8000/static/img/emojis/smile.png)**"]


def test_proccessor_invalid_emoji():
    result = emojify.EmojifyPreprocessor().run(["**:notvalidemoji:**"])
    assert result == ["**:notvalidemoji:**"]


def test_mentions_valid_username():
    with patch("taiga.mdrender.extensions.mentions.get_user_model") as get_user_model_mock:
        dummy_uuser = MagicMock()
        dummy_uuser.get_full_name.return_value = "Hermione Granger"
        get_user_model_mock.return_value.objects.get = MagicMock(return_value=dummy_uuser)

        result = render(dummy_project, "text @hermione text")

        get_user_model_mock.return_value.objects.get.assert_called_with(
            memberships__project_id=1,
            username="hermione",
        )
        assert result == ('<p>text <a class="mention" href="http://localhost:9001/profile/hermione" '
                          'title="Hermione Granger">@hermione</a> text</p>')


def test_mentions_valid_username_with_points():
    with patch("taiga.mdrender.extensions.mentions.get_user_model") as get_user_model_mock:
        dummy_uuser = MagicMock()
        dummy_uuser.get_full_name.return_value = "Luna Lovegood"
        get_user_model_mock.return_value.objects.get = MagicMock(return_value=dummy_uuser)

        result = render(dummy_project, "text @luna.lovegood text")

        get_user_model_mock.return_value.objects.get.assert_called_with(
            memberships__project_id=1,
            username="luna.lovegood",
        )
        assert result == ('<p>text <a class="mention" href="http://localhost:9001/profile/luna.lovegood" '
                          'title="Luna Lovegood">@luna.lovegood</a> text</p>')


def test_mentions_valid_username_with_dash():
    with patch("taiga.mdrender.extensions.mentions.get_user_model") as get_user_model_mock:
        dummy_uuser = MagicMock()
        dummy_uuser.get_full_name.return_value = "Ginny Weasley"
        get_user_model_mock.return_value.objects.get = MagicMock(return_value=dummy_uuser)

        result = render(dummy_project, "text @super-ginny text")

        get_user_model_mock.return_value.objects.get.assert_called_with(
            memberships__project_id=1,
            username="super-ginny",
        )
        assert result == ('<p>text <a class="mention" href="http://localhost:9001/profile/super-ginny" '
                          'title="Ginny Weasley">@super-ginny</a> text</p>')


def test_proccessor_valid_us_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "userstory"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#1**")
        expected_result = '<p><strong><a class="reference user-story" href="http://localhost:9001/project/test/us/1" title="#1 test">&num;1</a></strong></p>'
        assert result == expected_result


def test_proccessor_valid_issue_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "issue"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#2**")
        expected_result = '<p><strong><a class="reference issue" href="http://localhost:9001/project/test/issue/2" title="#2 test">&num;2</a></strong></p>'
        assert result == expected_result


def test_proccessor_valid_task_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "task"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#3**")
        expected_result = '<p><strong><a class="reference task" href="http://localhost:9001/project/test/task/3" title="#3 test">&num;3</a></strong></p>'
        assert result == expected_result


def test_proccessor_invalid_type_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "other"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#4**")
        assert result == "<p><strong>#4</strong></p>"


def test_proccessor_invalid_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        mock.return_value = None
        result = render(dummy_project, "**#5**")
        assert result == "<p><strong>#5</strong></p>"


def test_render_wiki_strong():
    assert render(dummy_project, "**test**") == "<p><strong>test</strong></p>"
    assert render(dummy_project, "__test__") == "<p><strong>test</strong></p>"


def test_render_wiki_italic():
    assert render(dummy_project, "*test*") == "<p><em>test</em></p>"
    assert render(dummy_project, "_test_") == "<p><em>test</em></p>"


def test_render_wiki_strike():
    assert render(dummy_project, "~~test~~") == "<p><del>test</del></p>"


def test_render_wikilink():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/test\" title=\"test\">test</a></p>"
    assert render(dummy_project, "[[test]]") == expected_result


def test_render_wikilink_1():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/test\" title=\"test\">test</a></p>"
    assert render(dummy_project, "[[test]]") == expected_result


def test_render_wikilink_2():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/test-page\" title=\"test page\">test page</a></p>"
    assert render(dummy_project, "[[test page]]") == expected_result


def test_render_wikilink_3():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/testpage\" title=\"TestPage\">TestPage</a></p>"
    assert render(dummy_project, "[[TestPage]]") == expected_result


def test_render_wikilink_with_custom_title():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/test\" title=\"custom\">custom</a></p>"
    assert render(dummy_project, "[[test|custom]]") == expected_result


def test_render_wikilink_slug_to_wikipages():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/wiki_page\" title=\"wiki page\">wiki</a></p>"
    assert render(dummy_project, "[wiki](wiki_page \"wiki page\")") == expected_result


def test_render_wikilink_relative_to_absolute():
    expected_result = "<p><a href=\"http://localhost:9001/project/test/\">test project</a></p>"
    assert render(dummy_project, "[test project](/project/test/)") == expected_result


def test_render_wikilink_obj_without_slug_absolute():
    expected_result = "<p><a href=\"http://localhost:9001/project/test/\">test project</a></p>"
    assert render(dummy_object, "[test project](/project/test/)") == expected_result


def test_render_wikilink_obj_without_slug_relative():
    expected_result = "<p><a class=\"reference wiki\" href=\"http://localhost:9001/project/test/wiki/wiki_page\">test project</a></p>"
    assert render(dummy_object, "[test project](wiki_page)") == expected_result


def test_render_reference_links():
    expected_result = "<p>An <a href=\"http://example.com/\" target=\"_blank\" title=\"Title\">example</a> of reference link</p>"
    source = "An [example][id] of reference link\n  [id]: http://example.com/  \"Title\""
    assert render(dummy_project, source) == expected_result


def test_render_url_autolinks():
    expected_result = "<p>Test the <a href=\"http://example.com/\" target=\"_blank\">http://example.com/</a> autolink</p>"
    source = "Test the http://example.com/ autolink"
    assert render(dummy_project, source) == expected_result


def test_render_url_autolinks_without_http():
    expected_result = "<p>Test the <a href=\"http://www.example.com\" target=\"_blank\">www.example.com</a> autolink</p>"
    source = "Test the www.example.com autolink"
    assert render(dummy_project, source) == expected_result


def test_render_url_autolinks_with_http():
    expected_result = "<p>Test the <a href=\"http://example.com/\" target=\"_blank\">http://example.com/</a> autolink</p>"
    source = "Test the http://example.com/ autolink"
    assert render(dummy_project, source) == expected_result


def test_render_url_autolinks_with_https():
    expected_result = "<p>Test the <a href=\"https://example.com/\" target=\"_blank\">https://example.com/</a> autolink</p>"
    source = "Test the https://example.com/ autolink"
    assert render(dummy_project, source) == expected_result


def test_render_url_autolinks_with_ftp():
    expected_result = "<p>Test the <a href=\"ftp://example.com/\" target=\"_blank\">ftp://example.com/</a> autolink</p>"
    source = "Test the ftp://example.com/ autolink"
    assert render(dummy_project, source) == expected_result


def test_render_url_automail():
    expected_result = "<p>Test the <a href=\"mailto:example@example.com\" target=\"_blank\">example@example.com</a> automail</p>"
    source = "Test the example@example.com automail"
    assert render(dummy_project, source) == expected_result


def test_render_url_automail_case_insensitive():
    expected_result = "<p>Test the <a href=\"mailto:eXAMPle+1@ExamplE.Com\" target=\"_blank\">eXAMPle+1@ExamplE.Com</a> automail</p>"
    source = "Test the eXAMPle+1@ExamplE.Com automail"
    assert render(dummy_project, source) == expected_result


def test_render_absolute_image():
    assert render(dummy_project, "![test](/test.png)") == "<p><img alt=\"test\" src=\"/test.png\"></p>"


def test_render_relative_image():
    assert render(dummy_project, "![test](test.png)") == "<p><img alt=\"test\" src=\"test.png\"></p>"


def test_render_triple_quote_code():
    expected_result = '<div class="codehilite"><pre><span></span><code><span class="nb">print</span><span class="p">(</span><span class="s2">&quot;test&quot;</span><span class="p">)</span>\n</code></pre></div>'

    assert render(dummy_project, "```python\nprint(\"test\")\n```") == expected_result


def test_render_triple_quote_and_lang_code():
    expected_result = '<div class="codehilite"><pre><span></span><code><span class="nb">print</span><span class="p">(</span><span class="s2">&quot;test&quot;</span><span class="p">)</span>\n</code></pre></div>'

    assert render(dummy_project, "```python\nprint(\"test\")\n```") == expected_result


def test_cache_by_sha():
    @cache_by_sha
    def test_cache(project, text):
        # Dummy function: ensure every invocation returns a different value
        return time.time()

    padding = "X" * 40  # Needed as cache is disabled for text under 40 chars

    result_a_1 = test_cache(dummy_project, "A" + padding)
    result_b_1 = test_cache(dummy_project, "B")
    result_a_2 = test_cache(dummy_project, "A" + padding)
    result_b_2 = test_cache(dummy_project, "B")

    assert result_a_1 != result_b_1  # Evidently
    assert result_b_1 != result_b_2  # No cached!
    assert result_a_1 == result_a_2  # Cached!


def test_get_diff_of_htmls_insertions():
    result = get_diff_of_htmls("", "<p>test</p>")
    assert result == "<ins style=\"background:#e6ffe6;\">&lt;p&gt;test&lt;/p&gt;</ins>"


def test_get_diff_of_htmls_deletions():
    result = get_diff_of_htmls("<p>test</p>", "")
    assert result == "<del style=\"background:#ffe6e6;\">&lt;p&gt;test&lt;/p&gt;</del>"


def test_get_diff_of_htmls_modifications():
    result = get_diff_of_htmls("<p>test1</p>", "<p>1test</p>")
    assert result == "<span>&lt;p&gt;</span><ins style=\"background:#e6ffe6;\">1</ins><span>test</span><del style=\"background:#ffe6e6;\">1</del><span>&lt;/p&gt;</span>"


def test_render_and_extract_references():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "issue"
        instance.content_object.subject = "test"
        (_, extracted) = render_and_extract(dummy_project, "**#1**")
        assert extracted['references'] == [instance.content_object]


def test_render_attachment_image(settings):
    settings.MEDIA_URL = "http://media.example.com/"
    attachment_url = "{}path/to/test.png#{}=us:42".format(settings.MEDIA_URL, REFRESH_PARAM)
    sentinel_url = "http://__sentinel__/"

    md = "![Test]({})".format(attachment_url)
    expected_result = "<p><img alt=\"Test\" src=\"{}#{}={}\"></p>".format(sentinel_url, REFRESH_PARAM, "us:42")

    with patch("taiga.mdrender.extensions.refresh_attachment.get_attachment_by_id") as mock:
        attachment = mock.return_value
        attachment.id = 42
        attachment.attached_file.url = sentinel_url

        result = render(dummy_project, md)

    assert result == expected_result
    assert mock.called is True
    mock.assert_called_with(dummy_project.id, 42)


def test_render_attachment_file(settings):
    settings.MEDIA_URL = "http://media.example.com/"
    attachment_url = "{}path/to/file.pdf#{}=us:42".format(settings.MEDIA_URL, REFRESH_PARAM)
    sentinel_url = "http://__sentinel__/"

    md = "[Test]({})".format(attachment_url)
    expected_result = "<p><a href=\"{}#{}={}\" target=\"_blank\">Test</a></p>".format(sentinel_url, REFRESH_PARAM, "us:42")

    with patch("taiga.mdrender.extensions.refresh_attachment.get_attachment_by_id") as mock:
        attachment = mock.return_value
        attachment.id = 42
        attachment.attached_file.url = sentinel_url

        result = render(dummy_project, md)

    assert result == expected_result
    assert mock.called is True
    mock.assert_called_with(dummy_project.id, 42)


def test_render_markdown_to_html():
    assert render(dummy_project, "- [x] test") == "<ul class=\"task-list\">\n<li class=\"task-list-item\"><label class=\"task-list-control\"><input checked type=\"checkbox\"><span class=\"task-list-indicator\"></span></label> test</li>\n</ul>"
