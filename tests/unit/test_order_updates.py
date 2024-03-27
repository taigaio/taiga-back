# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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


def test_apply_order_not_include_noop():
    orders = {
        "a": 1,
    }
    new_orders = {
        "a": 1,
    }
    apply_order_updates(orders, new_orders, remove_equal_original=True)
    assert orders == {}


def test_apply_order_put_it_first():
    orders = {
        "a": 0,
        "b": 1,
        "c": 2,
        "z": 99,
    }
    new_orders = {
        "z": 0,
    }
    apply_order_updates(orders, new_orders, remove_equal_original=True)
    assert orders == {
        "z": 0,
        "a": 1,
        "b": 2,
        "c": 3,
    }


def test_apply_order_put_it_first_with_tie():
    orders = {
        "a": 0,
        "b": 0,
        "c": 0,
        "d": 1,
        "z": 99,
    }
    new_orders = {
        "z": 0,
    }
    apply_order_updates(orders, new_orders, remove_equal_original=True)
    assert orders == {
        "z": 0,
        "a": 1,
        "b": 1,
        "c": 1,
        "d": 2,
    }


def test_apply_order_refresh():
    orders = {
        "a": 0,
        "b": 0,
        "c": 0,
        "d": 1,
        "w": 99,
        "z": 0,
    }
    new_orders = {
        "z": 0,
    }
    apply_order_updates(orders, new_orders, remove_equal_original=True)
    assert orders == {
        "a": 1,
        "b": 1,
        "c": 1,
        "d": 2,
        "w": 100,
    }


def test_apply_order_maintain_new_values():
    orders = {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
        "e": 7,
        "f": 6,
        "g": 7,
    }
    new_orders = {
        "e": 7,
        "g": 8,
    }
    expected = {"g": 8}
    apply_order_updates(orders, new_orders, remove_equal_original=True)
    assert expected == orders
