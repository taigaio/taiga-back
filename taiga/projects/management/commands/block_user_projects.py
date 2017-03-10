# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.core.management.base import BaseCommand
from taiga.projects.choices import BLOCKED_BY_NONPAYMENT
from taiga.projects.models import Project


class Command(BaseCommand):
    help = "Block user projects"

    def add_arguments(self, parser):
        parser.add_argument("owner_usernames",
                            nargs="+",
                            help="<owner_usernames owner_usernames ...>")

        parser.add_argument("--is-private",
                            dest="is_private")

        parser.add_argument("--blocked-code",
                            dest="blocked_code")

    def handle(self, *args, **options):
        owner_usernames = options["owner_usernames"]
        projects = Project.objects.filter(owner__username__in=owner_usernames)

        is_private = options.get("is_private")
        if is_private is not None:
            is_private = is_private.lower()
            is_private = is_private[0] in ["t", "y", "1"]
            projects = projects.filter(is_private=is_private)

        blocked_code = options.get("blocked_code")
        blocked_code = blocked_code if blocked_code is not None else BLOCKED_BY_NONPAYMENT
        projects.update(blocked_code=blocked_code)
