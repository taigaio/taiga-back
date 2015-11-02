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

from django.utils.encoding import force_text

from taiga.base.api.utils import encoders

import json


def dumps(data, ensure_ascii=True, encoder_class=encoders.JSONEncoder):
    return json.dumps(data, cls=encoder_class, indent=None, ensure_ascii=ensure_ascii)


def loads(data):
    if isinstance(data, bytes):
        data = force_text(data)
    return json.loads(data)

load = json.load

# Some backward compatibility that should
# be removed in near future.
to_json = dumps
from_json = loads
