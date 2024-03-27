# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

urls = {
    "home": "/",
    "discover": "/discover",
    "login": "/login",
    "register": "/register",
    "forgot-password": "/forgot-password",
    "new-project": "/project/new",
    "new-project-import": "/project/new/import/{0}",
    "settings-mail-notifications": "/user-settings/mail-notifications",

    "change-password": "/change-password/{0}", # user.token
    "change-email": "/change-email/{0}", # user.email_token
    "verify-email": "/verify-email/{0}", # user.email_token
    "cancel-account": "/cancel-account/{0}", # auth.tokens.CancelToken.for_user(user)
    "invitation": "/invitation/{0}", # membership.token

    "user": "/profile/{0}", # user.username

    "project": "/project/{0}", # project.slug

    "epics": "/project/{0}/epics/", # project.slug
    "epic": "/project/{0}/epic/{1}", # project.slug, epic.ref

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

    "project-import-jira": "/project/new/import/jira?url={}",
}
