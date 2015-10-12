# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
