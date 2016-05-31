# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.utils.translation import ugettext as _

from contextlib import contextmanager


@contextmanager
def without_signals(*disablers):
    for disabler in disablers:
        if not (isinstance(disabler, list) or isinstance(disabler, tuple)) or len(disabler) == 0:
            raise ValueError("The parameters must be lists of at least one parameter (the signal).")

        signal, *ids = disabler
        signal.backup_receivers = signal.receivers
        signal.receivers = list(filter(lambda x: x[0][0] not in ids, signal.receivers))

    try:
        yield
    except Exception as e:
        raise e
    finally:
        for disabler in disablers:
            signal, *ids = disabler
            signal.receivers = signal.backup_receivers
