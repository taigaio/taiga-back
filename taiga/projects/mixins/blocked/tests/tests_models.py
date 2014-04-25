# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
