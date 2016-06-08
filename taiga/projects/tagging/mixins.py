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


def _pre_save_new_tags_in_project_tagss_colors(obj):
    current_project_tags = [t[0] for t in obj.project.tags_colors]
    new_obj_tags = set()
    new_tags_colors = {}

    for tag in obj.tags:
        if isinstance(tag, (list, tuple)):
            name, color = tag

            if color and name not in current_project_tags:
                new_tags_colors[name] = color

            new_obj_tags.add(name)
        elif isinstance(tag, str):
            new_obj_tags.add(tag.lower())

    obj.tags = list(new_obj_tags)

    if new_tags_colors:
        obj.project.tags_colors += [[k, v] for k,v in new_tags_colors.items()]
        obj.project.save(update_fields=["tags_colors"])


class TaggedResourceMixin:
    def pre_save(self, obj):
        if obj.tags:
            _pre_save_new_tags_in_project_tagss_colors(obj)

        super().pre_save(obj)
