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


urls = {
    "home": "/",
    "discover": "/discover",
    "login": "/login",
    "register": "/register",
    "forgot-password": "/forgot-password",

    "change-password": "/change-password/{0}", # user.token
    "change-email": "/change-email/{0}", # user.email_token
    "cancel-account": "/cancel-account/{0}", # auth.token.get_token_for_user(user)
    "invitation": "/invitation/{0}", # membership.token

    "user": "/profile/{0}", # user.username

    "project": "/project/{0}", # project.slug

    "backlog": "/project/{0}/backlog/", # project.slug
    "taskboard": "/project/{0}/taskboard/{1}", # project.slug, milestone.slug
    "kanban": "/project/{0}/kanban/", # project.slug

    "userstory": "/project/{0}/us/{1}", # project.slug, us.ref
    "task": "/project/{0}/task/{1}", # project.slug, task.ref

    "issues": "/project/{0}/issues", # project.slug
    "issue": "/project/{0}/issue/{1}", # project.slug, issue.ref

    "wiki": "/project/{0}/wiki/{1}", # project.slug, wikipage.slug

    "team": "/project/{0}/team/", # project.slug

    "project-transfer": "/project/{0}/transfer/{1}", # project.slug, project.transfer_token

    "project-admin": "/login?next=/project/{0}/admin/project-profile/details", # project.slug
}
