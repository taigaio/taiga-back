# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

"""
Unit tests for EditableWatchedResourceSerializer watcher creation fix.

These tests verify the serializer-level logic in isolation using mocks,
without needing HTTP requests or a real database.

Bug fixed: watchers passed at creation time were silently discarded because
restore_object() returned early when instance=None (new object), before
add_watcher() could be called.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from taiga.projects.notifications.mixins import EditableWatchedResourceSerializer, WatchedResourceMixin


class TestRestoreObjectWatcherDeferral:
    """
    Unit tests for EditableWatchedResourceSerializer.restore_object().

    Verifies that:
    - On CREATE (instance=None): watcher IDs are stashed in _pending_watcher_ids
      instead of being discarded.
    - On UPDATE (instance is an object): watchers are applied immediately.
    - When no watchers are provided: nothing is stashed or applied.
    """

    def _make_serializer(self):
        """Build a minimal concrete subclass of EditableWatchedResourceSerializer."""
        serializer = EditableWatchedResourceSerializer.__new__(EditableWatchedResourceSerializer)
        serializer.fields = {}
        # validate_watchers is contributed by WatchersValidator at the concrete
        # subclass level (e.g. IssueValidator). Provide a no-op here so we can
        # test the serializer in isolation.
        serializer.validate_watchers = lambda attrs, source: attrs
        return serializer

    def test_restore_object_create_stashes_pending_watcher_ids(self):
        """
        On creation (instance=None), watchers must be stashed in
        _pending_watcher_ids and NOT discarded.
        """
        serializer = self._make_serializer()
        fake_obj = MagicMock()
        watcher_ids = [1, 2, 3]

        with patch(
            'taiga.base.api.serializers.ModelSerializer.restore_object',
            return_value=fake_obj
        ):
            attrs = {'watchers': watcher_ids, 'subject': 'Test'}
            result = serializer.restore_object(attrs, instance=None)

        # Object is returned
        assert result is fake_obj
        # Watcher IDs were stashed, not lost
        assert hasattr(serializer, '_pending_watcher_ids')
        assert set(serializer._pending_watcher_ids) == set(watcher_ids)
        # watchers must be removed from attrs before super() call (not a real model field)
        assert 'watchers' not in attrs

    def test_restore_object_create_no_watchers_nothing_stashed(self):
        """
        On creation with no watchers field, _pending_watcher_ids must not be set.
        """
        serializer = self._make_serializer()
        fake_obj = MagicMock()

        with patch(
            'taiga.base.api.serializers.ModelSerializer.restore_object',
            return_value=fake_obj
        ):
            attrs = {'subject': 'Test'}  # no 'watchers' key
            result = serializer.restore_object(attrs, instance=None)

        assert result is fake_obj
        # Nothing was stashed
        assert not getattr(serializer, '_pending_watcher_ids', None)

    def test_restore_object_update_applies_watchers_immediately(self):
        """
        On update (instance is not None), watchers must be applied immediately
        via add_watcher / remove_watcher — not deferred.
        """
        serializer = self._make_serializer()
        fake_instance = MagicMock()
        fake_obj = MagicMock()

        existing_user = MagicMock(id=10)
        fake_obj.get_watchers.return_value.values_list = MagicMock(return_value=[10])

        new_user = MagicMock(id=20)

        with patch(
            'taiga.base.api.serializers.ModelSerializer.restore_object',
            return_value=fake_obj
        ), patch(
            'taiga.projects.notifications.mixins.get_user_model'
        ) as mock_get_user_model, patch(
            'taiga.projects.notifications.mixins.services.add_watcher'
        ) as mock_add_watcher, patch(
            'taiga.projects.notifications.mixins.services.remove_watcher'
        ) as mock_remove_watcher:

            mock_get_user_model.return_value.objects.filter.side_effect = [
                [new_user],   # adding_users
                [],           # removing_users
            ]

            attrs = {'watchers': [20], 'subject': 'Test'}
            serializer.restore_object(attrs, instance=fake_instance)

        # add_watcher was called for the new watcher
        mock_add_watcher.assert_called_once_with(fake_obj, new_user)
        # Nothing was deferred
        assert not getattr(serializer, '_pending_watcher_ids', None)


class TestSaveAppliesPendingWatchers:
    """
    Unit tests for EditableWatchedResourceSerializer.save().

    Verifies that pending watchers stashed by restore_object() are correctly
    applied after the object is persisted (has a PK).
    """

    def _make_serializer_with_pending(self, pending_ids):
        serializer = EditableWatchedResourceSerializer.__new__(EditableWatchedResourceSerializer)
        serializer.fields = {}
        serializer._pending_watcher_ids = list(pending_ids)
        return serializer

    def test_save_applies_pending_watcher_ids(self):
        """
        After save(), watchers that were deferred during create must be
        applied via services.add_watcher().
        """
        watcher_user = MagicMock(id=5)
        saved_obj = MagicMock()
        saved_obj.get_watchers.return_value = [watcher_user]
        serializer = self._make_serializer_with_pending([5])

        with patch(
            'taiga.base.api.serializers.ModelSerializer.save',
            return_value=saved_obj
        ), patch(
            'taiga.projects.notifications.mixins.get_user_model'
        ) as mock_get_user_model, patch(
            'taiga.projects.notifications.mixins.services.add_watcher'
        ) as mock_add_watcher:

            mock_get_user_model.return_value.objects.filter.return_value = [watcher_user]

            result = serializer.save()

        # add_watcher was called with the persisted object and the user
        mock_add_watcher.assert_called_once_with(saved_obj, watcher_user)
        # Pending list is cleared after processing
        assert serializer._pending_watcher_ids is None
        # Returned object has watchers attribute set
        assert result is saved_obj

    def test_save_no_pending_watchers_does_not_call_add_watcher(self):
        """
        If no watchers were deferred (normal case without watchers in payload),
        add_watcher must NOT be called.
        """
        saved_obj = MagicMock()
        saved_obj.get_watchers.return_value = []
        serializer = EditableWatchedResourceSerializer.__new__(EditableWatchedResourceSerializer)
        serializer.fields = {}
        # No _pending_watcher_ids set

        with patch(
            'taiga.base.api.serializers.ModelSerializer.save',
            return_value=saved_obj
        ), patch(
            'taiga.projects.notifications.mixins.services.add_watcher'
        ) as mock_add_watcher:

            serializer.save()

        mock_add_watcher.assert_not_called()

    def test_save_clears_pending_after_applying(self):
        """
        _pending_watcher_ids must be reset to None after save() applies them,
        so a second save() call does not re-apply watchers.
        """
        watcher_user = MagicMock(id=7)
        saved_obj = MagicMock()
        saved_obj.get_watchers.return_value = [watcher_user]
        serializer = self._make_serializer_with_pending([7])

        with patch(
            'taiga.base.api.serializers.ModelSerializer.save',
            return_value=saved_obj
        ), patch(
            'taiga.projects.notifications.mixins.get_user_model'
        ) as mock_get_user_model, patch(
            'taiga.projects.notifications.mixins.services.add_watcher'
        ):
            mock_get_user_model.return_value.objects.filter.return_value = [watcher_user]
            serializer.save()

        assert serializer._pending_watcher_ids is None


class TestOldWatchersDefault:
    """
    Unit tests for WatchedResourceMixin._old_watchers default value.

    Before the fix, _old_watchers = None caused a TypeError in
    create_web_notifications_for_added_watchers() during creation:
        'watcher_id not in None'  →  TypeError
    """

    def test_old_watchers_default_is_empty_list_not_none(self):
        """
        _old_watchers must default to [] so membership tests
        (watcher_id not in self._old_watchers) never raise TypeError.
        """
        assert WatchedResourceMixin._old_watchers == []
        assert WatchedResourceMixin._old_watchers is not None

    def test_old_watchers_supports_membership_test(self):
        """
        Membership test on the default value must not raise TypeError.
        """
        mixin = WatchedResourceMixin()
        try:
            result = 99 not in mixin._old_watchers
        except TypeError:
            pytest.fail(
                "_old_watchers default caused TypeError on membership test. "
                "It must be [] not None."
            )
        assert result is True
