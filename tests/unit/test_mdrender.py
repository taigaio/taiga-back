from unittest import mock

import pytest

import taiga.base
from taiga.mdrender.processors import emoji
from taiga.mdrender.processors import mentions
from taiga.mdrender.processors import references

class DummyClass:
    pass

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

    DummyProject = DummyClass()
    DummyProject.id = 1
    DummyProject.slug = "test"

    result = references.references(DummyProject, "**#us1**")
    assert result == '**[#us1](/#/project/test/user-story/1 "test-subject")**'

    references.UserStory = UserStoryBack


def test_proccessor_invalid_us_reference():
    class MockModelEmpty:
        class objects:
            def filter(*args, **kwargs):
                return []

    DummyProject = DummyClass()
    DummyProject.id = 1
    DummyProject.slug = "test"

    UserStoryBack = references.UserStory
    references.UserStory = MockModelEmpty

    result = references.references(DummyProject, "**#us1**")
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

    DummyProject = DummyClass()
    DummyProject.id = 1
    DummyProject.slug = "test"

    result = references.references(DummyProject, "**#issue1**")
    assert result == '**[#issue1](/#/project/test/issues/1 "test-subject")**'

    references.Issue = IssueBack


def test_proccessor_invalid_issue_reference():
    class MockModelEmpty:
        class objects:
            def filter(*args, **kwargs):
                return []

    DummyProject = DummyClass()
    DummyProject.id = 1
    DummyProject.slug = "test"

    IssueBack = references.Issue
    references.Issue = MockModelEmpty

    result = references.references(DummyProject, "**#issue1**")
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

    DummyProject = DummyClass()
    DummyProject.id = 1
    DummyProject.slug = "test"

    result = references.references(DummyProject, "**#task1**")
    assert result == '**[#task1](/#/project/test/tasks/1 "test-subject")**'

    references.Task = TaskBack


def test_proccessor_invalid_task_reference():
    class MockModelEmpty:
        class objects:
            def filter(*args, **kwargs):
                return []

    DummyProject = DummyClass()
    DummyProject.id = 1
    DummyProject.slug = "test"

    TaskBack = references.Task
    references.Task = MockModelEmpty

    result = references.references(DummyProject, "**#task1**")
    assert result == "**#task1**"

    references.Task = TaskBack

def test_proccessor_invalid_type_reference():
    result = references.references(None, "**#invalid1**")
    assert result == "**#invalid1**"
