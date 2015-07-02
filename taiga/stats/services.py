# Copyright (C) 2015 Taiga Agile LLC <support@taiga.io>
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


from django.apps import apps


def get_total_projects():
    model = apps.get_model("projects", "Project")
    queryset =  model.objects.all()
    return queryset.count()


def grt_total_user_stories():
    model = apps.get_model("userstories", "UserStory")
    queryset =  model.objects.all()
    return queryset.count()


def get_total_issues():
    model = apps.get_model("issues", "Issue")
    queryset =  model.objects.all()
    return queryset.count()


def get_total_users(only_active=True, no_system=True):
    model = apps.get_model("users", "User")
    queryset =  model.objects.all()
    if only_active:
        queryset = queryset.filter(is_active=True)
    if no_system:
        queryset = queryset.filter(is_system=False)
    return queryset.count()
