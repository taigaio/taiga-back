# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.projects.services import apply_order_updates


def test_apply_order_updates_one_element_backward():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
        "e": 5,
        "f": 6
    }
    new_orders = {
        "d": 2
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "d": 2,
        "b": 3,
        "c": 4
    }


def test_apply_order_updates_one_element_forward():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
        "e": 5,
        "f": 6
    }
    new_orders = {
        "a": 3
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "a": 3,
        "c": 4,
        "d": 5,
        "e": 6,
        "f": 7
    }


def test_apply_order_updates_multiple_elements_backward():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
        "e": 5,
        "f": 6
    }
    new_orders = {
        "d": 2,
        "e": 3
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "d": 2,
        "e": 3,
        "b": 4,
        "c": 5
    }

def test_apply_order_updates_multiple_elements_forward():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
        "e": 5,
        "f": 6
    }
    new_orders = {
        "a": 4,
        "b": 5
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "a": 4,
        "b": 5,
        "d": 6,
        "e": 7,
        "f": 8
    }

def test_apply_order_updates_two_elements():
    orders = {
        "a": 0,
        "b": 1,
    }
    new_orders = {
        "b": 0
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "b": 0,
        "a": 1
    }

def test_apply_order_updates_duplicated_orders():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 3,
        "e": 3,
        "f": 4
    }
    new_orders = {
        "a": 3
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "a": 3,
        "c": 4,
        "d": 4,
        "e": 4,
        "f": 5
    }

def test_apply_order_updates_multiple_elements_duplicated_orders():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 3,
        "e": 3,
        "f": 4
    }
    new_orders = {
        "c": 3,
        "d": 3,
        "a": 4
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "c": 3,
        "d": 3,
        "a": 4,
        "e": 5,
        "f": 6
    }


def test_apply_order_invalid_new_order():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 3,
        "e": 3,
        "f": 4
    }
    new_orders = {
        "c": 3,
        "d": 3,
        "x": 3,
        "a": 4
    }
    apply_order_updates(orders, new_orders)
    assert orders == {
        "c": 3,
        "d": 3,
        "a": 4,
        "e": 5,
        "f": 6
    }
