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

from taiga.projects.services.tags_colors import update_project_tags_colors_handler, remove_unused_tags


####################################
# Signals over project items
####################################

## TAGS

def tags_normalization(sender, instance, **kwargs):
    if isinstance(instance.tags, (list, tuple)):
        instance.tags = list(map(str.lower, instance.tags))


def update_project_tags_when_create_or_edit_taggable_item(sender, instance, **kwargs):
    update_project_tags_colors_handler(instance)


def update_project_tags_when_delete_taggable_item(sender, instance, **kwargs):
    remove_unused_tags(instance.project)
    instance.project.save()
