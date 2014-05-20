from unittest import mock

import pytest

import taiga.base
from taiga.mdrender.processors import emoji
from taiga.mdrender.processors import mentions
from taiga.mdrender.processors import references
from taiga.mdrender.service import render

class DummyClass:
    pass

dummy_project = DummyClass()
dummy_project.id = 1
dummy_project.slug = "test"

def test_proccessor_valid_emoji():
    result = emoji.emoji("<b>:smile:</b>")
    assert result == '<b><img class="emoji" title="smile" alt="smile" height="20" width="20" src="http://localhost:8000/static/img/emojis/smile.png" align="top"></b>'

def test_proccessor_invalid_emoji():
    result = emoji.emoji("<b>:notvalidemoji:</b>")
    assert result == "<b>:notvalidemoji:</b>"

def test_proccessor_valid_user_mention():
    DummyModel = DummyClass()
    DummyModel.objects = DummyClass()
    DummyModel.objects.filter = lambda username: ["test"]

    mentions.User = DummyModel

    result = mentions.mentions("**@user1**")
    assert result == '**[@user1](/#/profile/user1 "@user1")**'

def test_proccessor_invalid_user_mention():
    DummyModel = DummyClass()
    DummyModel.objects = DummyClass()
    DummyModel.objects.filter = lambda username: []

    mentions.User = DummyModel

    result = mentions.mentions("**@notvaliduser**")
    assert result == '**@notvaliduser**'


def test_proccessor_valid_us_reference():
    class MockModelWithInstance:
        class objects:
            def filter(*args, **kwargs):
                dummy_instance = DummyClass()
                dummy_instance.subject = "test-subject"
                return [dummy_instance]
    UserStoryBack = references.UserStory
    references.UserStory = MockModelWithInstance

    result = references.references(dummy_project, "**#us1**")
    assert result == '**[#us1](/#/project/test/user-story/1 "test-subject")**'

    references.UserStory = UserStoryBack


def test_proccessor_invalid_us_reference():
    class MockModelEmpty:
        class objects:
            def filter(*args, **kwargs):
                return []

    UserStoryBack = references.UserStory
    references.UserStory = MockModelEmpty

    result = references.references(dummy_project, "**#us1**")
    assert result == "**#us1**"

    references.UserStory = UserStoryBack

def test_proccessor_valid_issue_reference():
    class MockModelWithInstance:
        class objects:
            def filter(*args, **kwargs):
                dummy_instance = DummyClass()
                dummy_instance.subject = "test-subject"
                return [dummy_instance]
    IssueBack = references.Issue
    references.Issue = MockModelWithInstance

    result = references.references(dummy_project, "**#issue1**")
    assert result == '**[#issue1](/#/project/test/issues/1 "test-subject")**'

    references.Issue = IssueBack


def test_proccessor_invalid_issue_reference():
    class MockModelEmpty:
        class objects:
            def filter(*args, **kwargs):
                return []

    IssueBack = references.Issue
    references.Issue = MockModelEmpty

    result = references.references(dummy_project, "**#issue1**")
    assert result == "**#issue1**"

    references.Issue = IssueBack

def test_proccessor_valid_task_reference():
    class MockModelWithInstance:
        class objects:
            def filter(*args, **kwargs):
                dummy_instance = DummyClass()
                dummy_instance.subject = "test-subject"
                return [dummy_instance]
    TaskBack = references.Task
    references.Task = MockModelWithInstance

    result = references.references(dummy_project, "**#task1**")
    assert result == '**[#task1](/#/project/test/tasks/1 "test-subject")**'

    references.Task = TaskBack


def test_proccessor_invalid_task_reference():
    class MockModelEmpty:
        class objects:
            def filter(*args, **kwargs):
                return []

    TaskBack = references.Task
    references.Task = MockModelEmpty

    result = references.references(dummy_project, "**#task1**")
    assert result == "**#task1**"

    references.Task = TaskBack

def test_proccessor_invalid_type_reference():
    result = references.references(dummy_project, "**#invalid1**")
    assert result == "**#invalid1**"

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
