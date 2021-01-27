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

from collections import namedtuple, OrderedDict


HistoryEntry = namedtuple('HistoryEntry', 'comment values_diff')


# These fields are ignored

EXCLUDED_FIELDS = (
    'description',
    'description_html',
    'blocked_note',
    'blocked_note_html',
    'content',
    'content_html',
    'epics_order',
    'backlog_order',
    'kanban_order',
    'sprint_order',
    'taskboard_order',
    'us_order',
    'custom_attributes',
    'tribe_gig',
)

# These fields can't be squashed because we don't have
# a squashing algorithm yet.

NON_SQUASHABLE_FIELDS = (
    'points',
    'attachments',
    'watchers',
    'description_diff',
    'content_diff',
    'blocked_note_diff',
    'custom_attributes',
)


def is_squashable(field):
    return field not in EXCLUDED_FIELDS and field not in NON_SQUASHABLE_FIELDS


def summary(field, entries):
    """
    Given an iterable of HistoryEntry of the same type return a summarized list.
    """
    if len(entries) <= 1:
        return entries

    # Apply squashing algorithm. In this case, get first `from` and last `to`.
    initial = entries[0].values_diff[field]
    final = entries[-1].values_diff[field]
    from_, to = initial[0], final[1]

    # If the resulting squashed `from` and `to` are equal we can skip
    # this entry completely

    return [] if from_ == to else [HistoryEntry('', {field: [from_, to]})]


def squash_history_entries(history_entries):
    """
    Given an iterable of HistoryEntry, squash them summarizing entries that have
    a squashable algorithm available.
    """
    history_entries = (HistoryEntry(entry.comment, entry.values_diff) for entry in history_entries)
    grouped = OrderedDict()
    for entry in history_entries:
        if entry.comment:
            yield entry
            continue

        for field, diff in entry.values_diff.items():
            if is_squashable(field):
                grouped.setdefault(field, [])
                grouped[field].append(HistoryEntry('', {field: diff}))
            else:
                yield HistoryEntry('', {field: diff})

    for field, entries in grouped.items():
        squashed = summary(field, entries)
        for entry in squashed:
            yield entry
