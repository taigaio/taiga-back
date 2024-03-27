# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from contextlib import closing
from django.db import connection
from django.db import ProgrammingError


def create(seqname:str, start=1) -> None:
    sql = "CREATE SEQUENCE {0} START %s".format(seqname)

    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [start])


def exists(seqname:str) -> bool:
    sql = """
    SELECT EXISTS(
      SELECT relname FROM pg_class
      WHERE relkind = 'S' AND relname = %s);
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [seqname])
        result = cursor.fetchone()
        return result[0]


def alter(seqname:str, value:int) -> None:
    sql = "SELECT setval(%s, %s);"
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [seqname, value])


def delete(seqname:str) -> None:
    sql = "DROP SEQUENCE {0};".format(seqname)
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql)

def next_value(seqname):
    sql = "SELECT nextval(%s);"
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [seqname])
        result = cursor.fetchone()
        return result[0]

def set_max(seqname, new_value):
    sql = "SELECT setval(%s, GREATEST(nextval(%s), %s));"
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, [seqname, seqname, new_value])
        result = cursor.fetchone()
        return result[0]
