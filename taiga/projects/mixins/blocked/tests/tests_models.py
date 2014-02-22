# -*- coding: utf-8 -*-

from django import test

from .foo.models import BlockedFoo


class BlockedMixinModelTestCase(test.TestCase):
    def test_block_item_without_note(self):
        obj = BlockedFoo.objects.create()
        self.assertEqual(BlockedFoo.objects.all().count(), 1)
        self.assertFalse(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")

        obj.is_blocked = True
        obj.save()
        self.assertTrue(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")

    def test_block_item_with_note(self):
        obj = BlockedFoo.objects.create()
        self.assertEqual(BlockedFoo.objects.all().count(), 1)
        self.assertFalse(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")

        obj.is_blocked = True
        obj.blocked_note = "Test note"
        obj.save()
        self.assertTrue(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "Test note")

    def test_unblock_item_withou_note(self):
        obj = BlockedFoo.objects.create(is_blocked=True)
        self.assertEqual(BlockedFoo.objects.all().count(), 1)
        self.assertTrue(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")

        obj.is_blocked = False
        obj.save()
        self.assertFalse(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")

    def test_unblock_item_with_note(self):
        obj = BlockedFoo.objects.create(is_blocked=True, blocked_note="Test note")
        self.assertEqual(BlockedFoo.objects.all().count(), 1)
        self.assertTrue(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "Test note")

        obj.is_blocked = False
        obj.save()
        self.assertFalse(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")

    def test_unblock_item_with_new_note(self):
        obj = BlockedFoo.objects.create(is_blocked=True, blocked_note="Test note")
        self.assertEqual(BlockedFoo.objects.all().count(), 1)
        self.assertTrue(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "Test note")

        obj.is_blocked = False
        obj.blocked_note = "New test note "
        obj.save()
        self.assertFalse(obj.is_blocked)
        self.assertEqual(obj.blocked_note, "")
