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
import sys

# Patch api view for correctly return 401 responses on
# request is authenticated instead of 403
from django.apps import AppConfig
from . import monkey

class BaseAppConfig(AppConfig):
    name = "taiga.base"
    verbose_name = "Base App Config"

    def ready(self):
        print("Monkey patching...", file=sys.stderr)
        monkey.patch_restframework()
        monkey.patch_serializer()

