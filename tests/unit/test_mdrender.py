# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from unittest.mock import patch, MagicMock

from taiga.mdrender.extensions import emojify
from taiga.mdrender.service import render, cache_by_sha, get_diff_of_htmls, render_and_extract

from datetime import datetime

dummy_project = MagicMock()
dummy_project.id = 1
dummy_project.slug = "test"


def test_proccessor_valid_emoji():
    result = emojify.EmojifyPreprocessor().run(["**:smile:**"])
    assert result == ["**![smile](http://localhost:8000/static/img/emojis/smile.png)**"]


def test_proccessor_invalid_emoji():
    result = emojify.EmojifyPreprocessor().run(["**:notvalidemoji:**"])
    assert result == ["**:notvalidemoji:**"]


def test_proccessor_valid_us_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "userstory"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#1**")
        expected_result = '<p><strong><a class="reference user-story" href="http://localhost:9001/project/test/us/1" title="#1 test">#1</a></strong></p>'
        assert result == expected_result


def test_proccessor_valid_issue_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "issue"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#2**")
        expected_result = '<p><strong><a class="reference issue" href="http://localhost:9001/project/test/issue/2" title="#2 test">#2</a></strong></p>'
        assert result == expected_result


def test_proccessor_valid_task_reference():
    with patch("taiga.mdrender.extensions.references.get_instance_by_ref") as mock:
        instance = mock.return_value
        instance.content_type.model = "task"
        instance.content_object.subject = "test"
        result = render(dummy_project, "**#3**")
        expected_result = '<p><strong><a class="reference task" href="http://localhost:9001/project/test/task/3" title="#3 test">#3</a></strong></p>'
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


def test_render_url_automail():
    expected_result = "<p>Test the <a href=\"mailto:example@example.com\" target=\"_blank\">example@example.com</a> automail</p>"
    source = "Test the example@example.com automail"
    assert render(dummy_project, source) == expected_result


def test_render_absolute_image():
    assert render(dummy_project, "![test](/test.png)") == "<p><img alt=\"test\" src=\"/test.png\"></p>"


def test_render_relative_image():
    assert render(dummy_project, "![test](test.png)") == "<p><img alt=\"test\" src=\"test.png\"></p>"


def test_render_triple_quote_code():
    expected_result = "<div class=\"codehilite\"><pre><span class=\"k\">print</span><span class=\"p\">(</span><span class=\"s\">\"test\"</span><span class=\"p\">)</span>\n</pre></div>"
    assert render(dummy_project, "```python\nprint(\"test\")\n```") == expected_result


def test_render_triple_quote_and_lang_code():
    expected_result = "<div class=\"codehilite\"><pre><span class=\"k\">print</span><span class=\"p\">(</span><span class=\"s\">\"test\"</span><span class=\"p\">)</span>\n</pre></div>"
    assert render(dummy_project, "```python\nprint(\"test\")\n```") == expected_result


def test_cache_by_sha():
    @cache_by_sha
    def test_cache(project, text):
        return datetime.now()

    result1 = test_cache(dummy_project, "test")
    result2 = test_cache(dummy_project, "test2")
    assert result1 != result2
    result3 = test_cache(dummy_project, "test")
    assert result1 == result3


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
