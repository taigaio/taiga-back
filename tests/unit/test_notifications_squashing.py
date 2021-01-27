# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

from taiga.projects.notifications import squashing


def assert_(expected, squashed, *, ordered=True):
    """
    Check if expected entries are the same as the squashed.

    Allow to specify if they must maintain the order or conversely they can
    appear in any order.
    """
    squashed = list(squashed)
    assert len(expected) == len(squashed)
    if ordered:
        assert expected == squashed
    else:
        # Can't use a set, just check all of the squashed entries
        # are in the expected ones.
        for entry in squashed:
            assert entry in expected


def test_squash_omits_comments():
    history_entries = [
        squashing.HistoryEntry(comment='A', values_diff={'status': ['A', 'B']}),
        squashing.HistoryEntry(comment='B', values_diff={'status': ['B', 'C']}),
        squashing.HistoryEntry(comment='C', values_diff={'status': ['C', 'B']}),
    ]
    squashed = squashing.squash_history_entries(history_entries)
    assert_(history_entries, squashed)


def test_squash_allowed_grouped_at_the_end():
    history_entries = [
        squashing.HistoryEntry(comment='A', values_diff={}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['A', 'B']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['B', 'C']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['C', 'D']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['D', 'C']}),
        squashing.HistoryEntry(comment='Z', values_diff={}),
    ]
    expected = [
        squashing.HistoryEntry(comment='A', values_diff={}),
        squashing.HistoryEntry(comment='Z', values_diff={}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['A', 'C']}),
    ]

    squashed = squashing.squash_history_entries(history_entries)
    assert_(expected, squashed)


def test_squash_remove_noop_changes():
    history_entries = [
        squashing.HistoryEntry(comment='', values_diff={'status': ['A', 'B']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['B', 'A']}),
    ]
    expected = []

    squashed = squashing.squash_history_entries(history_entries)
    assert_(expected, squashed)


def test_squash_remove_noop_changes_but_maintain_others():
    history_entries = [
        squashing.HistoryEntry(comment='', values_diff={'status': ['A', 'B'], 'type': ['1', '2']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['B', 'A']}),
    ]
    expected = [
        squashing.HistoryEntry(comment='', values_diff={'type': ['1', '2']}),
    ]

    squashed = squashing.squash_history_entries(history_entries)
    assert_(expected, squashed)


def test_squash_values_diff_with_multiple_fields():
    history_entries = [
        squashing.HistoryEntry(comment='', values_diff={'status': ['A', 'B'], 'type': ['1', '2']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['B', 'C']}),
    ]
    expected = [
        squashing.HistoryEntry(comment='', values_diff={'type': ['1', '2']}),
        squashing.HistoryEntry(comment='', values_diff={'status': ['A', 'C']}),
    ]

    squashed = squashing.squash_history_entries(history_entries)
    assert_(expected, squashed, ordered=False)


def test_squash_arrays():
    history_entries = [
        squashing.HistoryEntry(comment='', values_diff={'tags': [['A', 'B'], ['A']]}),
        squashing.HistoryEntry(comment='', values_diff={'tags': [['A'], ['A', 'C']]}),
    ]
    expected = [
        squashing.HistoryEntry(comment='', values_diff={'tags': [['A', 'B'], ['A', 'C']]}),
    ]

    squashed = squashing.squash_history_entries(history_entries)
    assert_(expected, squashed, ordered=False)
