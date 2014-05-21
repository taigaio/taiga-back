from unittest.mock import patch, MagicMock

import pytest

import taiga.base
from taiga.mdrender.extensions import mentions
from taiga.mdrender.extensions import emojify
from taiga.mdrender.service import render

from taiga.projects.references import services

from taiga.users.models import User

dummy_project = MagicMock()
dummy_project.id = 1
dummy_project.slug = "test"

def test_proccessor_valid_emoji():
    result = emojify.EmojifyPreprocessor().run(["**:smile:**"])
    assert result == ["**![smile](http://localhost:8000/static/img/emojis/smile.png)**"]

def test_proccessor_invalid_emoji():
    result = emojify.EmojifyPreprocessor().run(["**:notvalidemoji:**"])
    assert result == ["**:notvalidemoji:**"]

def test_proccessor_valid_user_mention():
    with patch("taiga.mdrender.extensions.mentions.User") as mock:
        instance = mock.objects.get.return_value
        instance.get_full_name.return_value = "test name"
        result = render(dummy_project, "**@user1**")
        expected_result = "<p><strong><a alt=\"test name\" class=\"mention\" href=\"/#/profile/user1\" title=\"test name\">&commat;user1</a></strong></p>"
        assert result == expected_result

def test_proccessor_invalid_user_mention():
    with patch("taiga.mdrender.extensions.mentions.User") as mock:
        mock.DoesNotExist = User.DoesNotExist
        mock.objects.get.side_effect = User.DoesNotExist
        result = render(dummy_project, "**@notvaliduser**")
        assert result == '<p><strong>@notvaliduser</strong></p>'

def test_proccessor_valid_us_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "userstory"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#1**")
        expected_result = '<p><strong><a alt="test" class="reference user-story" href="/#/project/test/user-story/1" title="test">&num;1</a></strong></p>'
        assert result == expected_result

def test_proccessor_valid_issue_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "issue"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#1**")
        expected_result = '<p><strong><a alt="test" class="reference issue" href="/#/project/test/issues/1" title="test">&num;1</a></strong></p>'
        assert result == expected_result

def test_proccessor_valid_task_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "task"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#1**")
        expected_result = '<p><strong><a alt="test" class="reference task" href="/#/project/test/tasks/1" title="test">&num;1</a></strong></p>'
        assert result == expected_result

def test_proccessor_invalid_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        mock.return_value = None
        result = render(dummy_project, "**#1**")
        assert result == "<p><strong>#1</strong></p>"

def test_render_wiki_strong():
    assert render(dummy_project, "**test**") == "<p><strong>test</strong></p>"
    assert render(dummy_project, "__test__") == "<p><strong>test</strong></p>"

def test_render_wiki_italic():
    assert render(dummy_project, "*test*") == "<p><em>test</em></p>"
    assert render(dummy_project, "_test_") == "<p><em>test</em></p>"

def test_render_wiki_strike():
    assert render(dummy_project, "~~test~~") == "<p><del>test</del></p>"

def test_render_absolute_link():
    assert render(dummy_project, "[test](/test)") == "<p><a href=\"/test\">test</a></p>"

def test_render_relative_link():
    assert render(dummy_project, "[test](test)") == "<p><a href=\"test\">test</a></p>"

def test_render_wikilink():
    expected_result = "<p><a class=\"wikilink\" href=\"#/project/test/wiki/test\">test</a></p>"
    assert render(dummy_project, "[[test]]") == expected_result

def test_render_wikilink_with_custom_title():
    expected_result = "<p><a class=\"wikilink\" href=\"#/project/test/wiki/test\">custom</a></p>"
    assert render(dummy_project, "[[test|custom]]") == expected_result

def test_render_reference_links():
    expected_result = "<p>An <a href=\"http://example.com/\" title=\"Title\">example</a> of reference link</p>"
    source = "An [example][id] of reference link\n  [id]: http://example.com/  \"Title\""
    assert render(dummy_project, source) == expected_result

def test_render_url_autolinks():
    expected_result = "<p>Test the <a href=\"http://example.com/\">http://example.com/</a> autolink</p>"
    source = "Test the http://example.com/ autolink"
    assert render(dummy_project, source) == expected_result

def test_render_absolute_image():
    assert render(dummy_project, "![test](/test.png)") == "<p><img alt=\"test\" src=\"/test.png\" /></p>"

def test_render_relative_image():
    assert render(dummy_project, "![test](test.png)") == "<p><img alt=\"test\" src=\"test.png\" /></p>"

def test_render_triple_quote_code():
    expected_result = "<div class=\"codehilite\"><pre><span class=\"n\">print</span><span class=\"p\">(</span><span class=\"s\">&quot;test&quot;</span><span class=\"p\">)</span>\n</pre></div>"
    assert render(dummy_project, "```\nprint(\"test\")\n```") == expected_result

def test_render_triple_quote_and_lang_code():
    expected_result = "<div class=\"codehilite\"><pre><span class=\"k\">print</span><span class=\"p\">(</span><span class=\"s\">&quot;test&quot;</span><span class=\"p\">)</span>\n</pre></div>"
    assert render(dummy_project, "```python\nprint(\"test\")\n```") == expected_result
