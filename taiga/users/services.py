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

"""
This model contains a domain logic for users application.
"""
from io import StringIO
import csv
import os
import uuid
import zipfile


from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db.models import OuterRef, Q, Subquery
from django.db import connection
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError

from taiga.base import exceptions as exc
from taiga.base.utils.db import to_tsquery
from taiga.base.utils.urls import get_absolute_url
from taiga.projects.notifications.choices import NotifyLevel
from taiga.projects.notifications.services import get_projects_watched


def get_user_by_username_or_email(username_or_email):
    user_model = get_user_model()
    qs = user_model.objects.filter(Q(username__iexact=username_or_email) |
                                   Q(email__iexact=username_or_email))

    if len(qs) > 1:
        qs = qs.filter(Q(username=username_or_email) |
                       Q(email=username_or_email))

    if len(qs) == 0:
        raise exc.WrongArguments(_("Username or password does not matches user."))

    user = qs[0]
    return user


def get_and_validate_user(*, username: str, password: str) -> bool:
    """
    Check if user with username/email exists and specified
    password matchs well with existing user password.

    if user is valid,  user is returned else, corresponding
    exception is raised.
    """

    user = get_user_by_username_or_email(username)
    if not user.check_password(password):
        raise exc.WrongArguments(_("Username or password does not matches user."))

    return user


def get_photo_url(photo):
    """Get a photo absolute url and the photo automatically cropped."""
    if not photo:
        return None
    try:
        url = get_thumbnailer(photo)[settings.THN_AVATAR_SMALL].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None


def get_user_photo_url(user):
    """Get the user's photo url."""
    if not user:
        return None
    return get_photo_url(user.photo)


def get_big_photo_url(photo):
    """Get a big photo absolute url and the photo automatically cropped."""
    if not photo:
        return None
    try:
        url = get_thumbnailer(photo)[settings.THN_AVATAR_BIG].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None


def get_user_big_photo_url(user):
    """Get the user's big photo url."""
    if not user:
        return None
    return get_big_photo_url(user.photo)


def get_visible_project_ids(from_user, by_user):
    """Calculate the project_ids from one user visible by another"""
    required_permissions = ["view_project"]
    # Or condition for membership filtering, the basic one is the access to projects
    # allowing anonymous visualization
    member_perm_conditions = Q(project__anon_permissions__contains=required_permissions)

    # Authenticated
    if by_user.is_authenticated:
        # Calculating the projects wich from_user user is member
        by_user_project_ids = by_user.memberships.values_list("project__id", flat=True)
        # Adding to the condition two OR situations:
        # - The from user has a role that allows access to the project
        # - The to user is the owner
        member_perm_conditions |= \
            Q(project__id__in=by_user_project_ids, role__permissions__contains=required_permissions) |\
            Q(project__id__in=by_user_project_ids, is_admin=True)

    Membership = apps.get_model('projects', 'Membership')
    # Calculating the user memberships adding the permission filter for the by user
    memberships_qs = Membership.objects.filter(member_perm_conditions, user=from_user)
    project_ids = memberships_qs.values_list("project__id", flat=True)
    return project_ids


def get_stats_for_user(from_user, by_user):
    """Get the user stats"""
    project_ids = get_visible_project_ids(from_user, by_user)

    total_num_projects = len(project_ids)

    role_names = from_user.memberships.filter(project__id__in=project_ids).values_list("role__name", flat=True)
    roles = [_(r) for r in role_names]
    roles = list(set(roles))

    User = apps.get_model('users', 'User')
    total_num_contacts = User.objects.filter(memberships__project__id__in=project_ids)\
        .exclude(id=from_user.id)\
        .distinct()\
        .count()

    UserStory = apps.get_model('userstories', 'UserStory')

    assigned_users_ids = UserStory.objects.order_by().filter(
        assigned_users__in=[from_user], id=OuterRef('pk')).values('pk')

    total_num_closed_userstories = UserStory.objects.filter(
        is_closed=True,
        project__id__in=project_ids).filter(
        Q(assigned_to=from_user) | Q(pk__in=Subquery(assigned_users_ids))).count()

    project_stats = {
        'total_num_projects': total_num_projects,
        'roles': roles,
        'total_num_contacts': total_num_contacts,
        'total_num_closed_userstories': total_num_closed_userstories,
    }
    return project_stats


def get_liked_content_for_user(user):
    """Returns a dict where:
        - The key is the content_type model
        - The values are list of id's of the different objects liked by the user
    """
    if user.is_anonymous:
        return {}

    user_likes = {}
    for (ct_model, object_id) in user.likes.values_list("content_type__model", "object_id"):
        list = user_likes.get(ct_model, [])
        list.append(object_id)
        user_likes[ct_model] = list

    return user_likes


def get_voted_content_for_user(user):
    """Returns a dict where:
        - The key is the content_type model
        - The values are list of id's of the different objects voted by the user
    """
    if user.is_anonymous:
        return {}

    user_votes = {}
    for (ct_model, object_id) in user.votes.values_list("content_type__model", "object_id"):
        list = user_votes.get(ct_model, [])
        list.append(object_id)
        user_votes[ct_model] = list

    return user_votes


def get_watched_content_for_user(user):
    """Returns a dict where:
        - The key is the content_type model
        - The values are list of id's of the different objects watched by the user
    """
    if user.is_anonymous:
        return {}

    user_watches = {}
    for (ct_model, object_id) in user.watched.values_list("content_type__model", "object_id"):
        list = user_watches.get(ct_model, [])
        list.append(object_id)
        user_watches[ct_model] = list

    # Now for projects,
    projects_watched = get_projects_watched(user)
    project_content_type_model = ContentType.objects.get(app_label="projects", model="project").model
    user_watches[project_content_type_model] = projects_watched.values_list("id", flat=True)

    return user_watches


def _build_watched_sql_for_projects(for_user):
    sql = """
    SELECT projects_project.id AS id, null::integer AS ref, 'project'::text AS type,
        tags, notifications_notifypolicy.project_id AS object_id, projects_project.id AS project,
        slug, projects_project.name, null::text AS subject,
        notifications_notifypolicy.created_at as created_date,
        coalesce(watchers, 0) AS total_watchers, projects_project.total_fans AS total_fans, null::integer AS total_voters,
        null::integer AS assigned_to, null::text as status, null::text as status_color
        FROM notifications_notifypolicy
        INNER JOIN projects_project
            ON (projects_project.id = notifications_notifypolicy.project_id)
        LEFT JOIN (SELECT project_id, count(*) watchers
                   FROM notifications_notifypolicy
                   WHERE notifications_notifypolicy.notify_level != {none_notify_level}
                   GROUP BY project_id
                ) type_watchers
            ON projects_project.id = type_watchers.project_id
        WHERE
              notifications_notifypolicy.user_id = {for_user_id}
              AND notifications_notifypolicy.notify_level != {none_notify_level}
    """
    sql = sql.format(
        for_user_id=for_user.id,
        none_notify_level=NotifyLevel.none,
        project_content_type_id=ContentType.objects.get(app_label="projects", model="project").id)
    return sql


def _build_liked_sql_for_projects(for_user):
    sql = """
    SELECT projects_project.id AS id, null::integer AS ref, 'project'::text AS type,
        tags, likes_like.object_id AS object_id, projects_project.id AS project,
        slug, projects_project.name, null::text AS subject,
        likes_like.created_date,
        coalesce(watchers, 0) AS total_watchers, projects_project.total_fans AS total_fans,
        null::integer AS assigned_to, null::text as status, null::text as status_color
        FROM likes_like
        INNER JOIN projects_project
              ON (projects_project.id = likes_like.object_id)
        LEFT JOIN (SELECT project_id, count(*) watchers
                   FROM notifications_notifypolicy
                   WHERE notifications_notifypolicy.notify_level != {none_notify_level}
                   GROUP BY project_id
                ) type_watchers
              ON projects_project.id = type_watchers.project_id
        WHERE likes_like.user_id = {for_user_id} AND {project_content_type_id} = likes_like.content_type_id
    """
    sql = sql.format(
        for_user_id=for_user.id,
        none_notify_level=NotifyLevel.none,
        project_content_type_id=ContentType.objects.get(app_label="projects", model="project").id)

    return sql


def _build_sql_for_type(for_user, type, table_name, action_table, ref_column="ref",
                        project_column="project_id", assigned_to_column="assigned_to_id",
                        slug_column="slug", subject_column="subject"):
    sql = """
    SELECT {table_name}.id AS id, {ref_column} AS ref, '{type}' AS type,
        tags, {action_table}.object_id AS object_id, {table_name}.{project_column} AS project,
        {slug_column} AS slug, null AS name, {subject_column} AS subject,
        {action_table}.created_date,
        coalesce(watchers, 0) AS total_watchers, null::integer AS total_fans, coalesce(votes_votes.count, 0) AS total_voters,
        {assigned_to_column}  AS assigned_to, projects_{type}status.name as status, projects_{type}status.color as status_color
        FROM {action_table}
        INNER JOIN django_content_type
              ON ({action_table}.content_type_id = django_content_type.id AND django_content_type.model = '{type}')
        INNER JOIN {table_name}
              ON ({table_name}.id = {action_table}.object_id)
        INNER JOIN projects_{type}status
              ON (projects_{type}status.id = {table_name}.status_id)
        LEFT JOIN (SELECT object_id, content_type_id, count(*) watchers FROM notifications_watched GROUP BY object_id, content_type_id) type_watchers
              ON {table_name}.id = type_watchers.object_id AND django_content_type.id = type_watchers.content_type_id
        LEFT JOIN votes_votes
              ON ({table_name}.id = votes_votes.object_id AND django_content_type.id = votes_votes.content_type_id)
        WHERE {action_table}.user_id = {for_user_id}
    """
    sql = sql.format(for_user_id=for_user.id, type=type, table_name=table_name,
                     action_table=action_table, ref_column=ref_column,
                     project_column=project_column, assigned_to_column=assigned_to_column,
                     slug_column=slug_column, subject_column=subject_column)

    return sql


def get_watched_list(for_user, from_user, type=None, q=None):
    filters_sql = ""

    if type:
        filters_sql += " AND type = %(type)s "

    if q:
        filters_sql += """ AND (
            to_tsvector('simple', coalesce(subject,'') || ' ' ||coalesce(entities.name,'') || ' ' ||coalesce(to_char(ref, '999'),'')) @@ to_tsquery('simple', %(q)s)
        )
        """

    sql = """
    -- BEGIN Basic info: we need to mix info from different tables and denormalize it
    SELECT entities.*,
           projects_project.name as project_name, projects_project.description as description, projects_project.slug as project_slug, projects_project.is_private as project_is_private,
           projects_project.blocked_code as project_blocked_code, projects_project.tags_colors, projects_project.logo,
           users_user.id as assigned_to_id,
           row_to_json(users_user) as assigned_to_extra_info

        FROM (
            {epics_sql}
            UNION
            {userstories_sql}
            UNION
            {tasks_sql}
            UNION
            {issues_sql}
            UNION
            {projects_sql}
        ) as entities
    -- END Basic info

    -- BEGIN Project info
    LEFT JOIN projects_project
        ON (entities.project = projects_project.id)
    -- END Project info

    -- BEGIN Assigned to user info
    LEFT JOIN users_user
        ON (assigned_to = users_user.id)
    -- END Assigned to user info

    -- BEGIN Permissions checking
    LEFT JOIN projects_membership
        -- Here we check the memberbships from the user requesting the info
        ON (projects_membership.user_id = {from_user_id} AND projects_membership.project_id = entities.project)

    LEFT JOIN users_role
        ON (entities.project = users_role.project_id AND users_role.id =  projects_membership.role_id)

    WHERE
        -- public project
        (
            projects_project.is_private = false
            OR(
                -- private project where the view_ permission is included in the user role for that project or in the anon permissions
                projects_project.is_private = true
                AND(
                    (entities.type = 'issue' AND 'view_issues' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'task' AND 'view_tasks' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'userstory' AND 'view_us' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'project' AND 'view_project' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'epic' AND 'view_epic' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                )
        ))
    -- END Permissions checking
        {filters_sql}

    ORDER BY entities.created_date DESC;
    """

    from_user_id = -1
    if not from_user.is_anonymous:
        from_user_id = from_user.id

    sql = sql.format(
        for_user_id=for_user.id,
        from_user_id=from_user_id,
        filters_sql=filters_sql,
        userstories_sql=_build_sql_for_type(for_user, "userstory", "userstories_userstory", "notifications_watched", slug_column="null"),
        tasks_sql=_build_sql_for_type(for_user, "task", "tasks_task", "notifications_watched", slug_column="null"),
        issues_sql=_build_sql_for_type(for_user, "issue", "issues_issue", "notifications_watched", slug_column="null"),
        epics_sql=_build_sql_for_type(for_user, "epic", "epics_epic", "notifications_watched", slug_column="null"),
        projects_sql=_build_watched_sql_for_projects(for_user))

    cursor = connection.cursor()
    params = {
        "type": type,
        "q": to_tsquery(q) if q is not None else ""
    }
    cursor.execute(sql, params)

    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def get_liked_list(for_user, from_user, type=None, q=None):
    filters_sql = ""

    if type:
        filters_sql += " AND type = %(type)s "

    if q:
        filters_sql += """ AND (
            to_tsvector('simple', coalesce(subject,'') || ' ' ||coalesce(entities.name,'') || ' ' ||coalesce(to_char(ref, '999'),'')) @@ to_tsquery('simple', %(q)s)
        )
        """

    sql = """
    -- BEGIN Basic info: we need to mix info from different tables and denormalize it
    SELECT entities.*,
           projects_project.name as project_name, projects_project.description as description, projects_project.slug as project_slug, projects_project.is_private as project_is_private,
           projects_project.blocked_code as project_blocked_code, projects_project.tags_colors, projects_project.logo,
           users_user.id as assigned_to_id,
           row_to_json(users_user) as assigned_to_extra_info
        FROM (
            {projects_sql}
        ) as entities
    -- END Basic info

    -- BEGIN Project info
    LEFT JOIN projects_project
        ON (entities.project = projects_project.id)
    -- END Project info

    -- BEGIN Assigned to user info
    LEFT JOIN users_user
        ON (assigned_to = users_user.id)
    -- END Assigned to user info

    -- BEGIN Permissions checking
    LEFT JOIN projects_membership
        -- Here we check the memberbships from the user requesting the info
        ON (projects_membership.user_id = {from_user_id} AND projects_membership.project_id = entities.project)

    LEFT JOIN users_role
        ON (entities.project = users_role.project_id AND users_role.id =  projects_membership.role_id)

    WHERE
        -- public project
        (
            projects_project.is_private = false
            OR(
                -- private project where the view_ permission is included in the user role for that project or in the anon permissions
                projects_project.is_private = true
                AND(
                    'view_project' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions))
                )
        ))
    -- END Permissions checking
        {filters_sql}

    ORDER BY entities.created_date DESC;
    """

    from_user_id = -1
    if not from_user.is_anonymous:
        from_user_id = from_user.id

    sql = sql.format(
        for_user_id=for_user.id,
        from_user_id=from_user_id,
        filters_sql=filters_sql,
        projects_sql=_build_liked_sql_for_projects(for_user))

    cursor = connection.cursor()
    params = {
        "type": type,
        "q": to_tsquery(q) if q is not None else ""
    }
    cursor.execute(sql, params)

    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def get_voted_list(for_user, from_user, type=None, q=None):
    filters_sql = ""

    if type:
        filters_sql += " AND type = %(type)s "

    if q:
        filters_sql += """ AND (
            to_tsvector('simple', coalesce(subject,'') || ' ' ||coalesce(entities.name,'') || ' ' ||coalesce(to_char(ref, '999'),'')) @@ to_tsquery('simple', %(q)s)
        )
        """

    sql = """
    -- BEGIN Basic info: we need to mix info from different tables and denormalize it
    SELECT entities.*,
           projects_project.name as project_name, projects_project.description as description, projects_project.slug as project_slug, projects_project.is_private as project_is_private,
           projects_project.blocked_code as project_blocked_code, projects_project.tags_colors, projects_project.logo,
           users_user.id as assigned_to_id,
           row_to_json(users_user) as assigned_to_extra_info
        FROM (
            {epics_sql}
            UNION
            {userstories_sql}
            UNION
            {tasks_sql}
            UNION
            {issues_sql}
        ) as entities
    -- END Basic info

    -- BEGIN Project info
    LEFT JOIN projects_project
        ON (entities.project = projects_project.id)
    -- END Project info

    -- BEGIN Assigned to user info
    LEFT JOIN users_user
        ON (assigned_to = users_user.id)
    -- END Assigned to user info

    -- BEGIN Permissions checking
    LEFT JOIN projects_membership
        -- Here we check the memberbships from the user requesting the info
        ON (projects_membership.user_id = {from_user_id} AND projects_membership.project_id = entities.project)

    LEFT JOIN users_role
        ON (entities.project = users_role.project_id AND users_role.id =  projects_membership.role_id)

    WHERE
        -- public project
        (
            projects_project.is_private = false
            OR(
                -- private project where the view_ permission is included in the user role for that project or in the anon permissions
                projects_project.is_private = true
                AND(
                    (entities.type = 'issue' AND 'view_issues' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'task' AND 'view_tasks' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'userstory' AND 'view_us' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                    OR (entities.type = 'epic' AND 'view_epic' = ANY (array_cat(users_role.permissions, projects_project.anon_permissions)))
                )
        ))
    -- END Permissions checking
        {filters_sql}

    ORDER BY entities.created_date DESC;
    """

    from_user_id = -1
    if not from_user.is_anonymous:
        from_user_id = from_user.id

    sql = sql.format(
        for_user_id=for_user.id,
        from_user_id=from_user_id,
        filters_sql=filters_sql,
        userstories_sql=_build_sql_for_type(for_user, "userstory", "userstories_userstory", "votes_vote", slug_column="null"),
        tasks_sql=_build_sql_for_type(for_user, "task", "tasks_task", "votes_vote", slug_column="null"),
        issues_sql=_build_sql_for_type(for_user, "issue", "issues_issue", "votes_vote", slug_column="null"),
        epics_sql=_build_sql_for_type(for_user, "epic", "epics_epic", "votes_vote", slug_column="null"))

    cursor = connection.cursor()
    params = {
        "type": type,
        "q": to_tsquery(q) if q is not None else ""
    }
    cursor.execute(sql, params)

    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def has_available_slot_for_new_project(owner, is_private, total_memberships):
    if is_private:
        current_projects = owner.owned_projects.filter(is_private=True).count()
        max_projects = owner.max_private_projects
        error_project_exceeded =  _("You can't have more private projects")

        max_memberships = owner.max_memberships_private_projects
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        current_projects = owner.owned_projects.filter(is_private=False).count()
        max_projects = owner.max_public_projects
        error_project_exceeded = _("You can't have more public projects")

        max_memberships = owner.max_memberships_public_projects
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded)

    if max_memberships is not None and total_memberships > max_memberships:
        return (False, error_memberships_exceeded)

    return (True, None)


def render_profile(user, outfile):
    csv_data = StringIO()
    fieldnames = ["username", "email", "full_name", "bio"]

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()

    user_data = {}
    for fieldname in fieldnames:
        user_data[fieldname] = getattr(user, fieldname, '')

    writer.writerow(user_data)

    outfile.write(csv_data.getvalue().encode())


def export_profile(user):
    filename = "{}-{}".format(user.username, uuid.uuid4().hex)

    csv_path = "exports/{}/{}.csv".format(user.pk, filename)
    zip_path = "exports/{}/{}.zip".format(user.pk, filename)

    with default_storage.open(csv_path, mode="wb") as output:
        render_profile(user, output)
        output.close()

    zf = zipfile.ZipFile(default_storage.path(zip_path), "w", zipfile.ZIP_DEFLATED)

    zf.write(default_storage.path(csv_path), "{}-profile.csv".format(filename))
    os.remove(default_storage.path(csv_path))

    if user.photo:
        _, file_extension = os.path.splitext(default_storage.path(user.photo.name))
        zf.write(default_storage.path(user.photo.name),
                 "{}-photo{}".format(filename, file_extension))

    return default_storage.url(zip_path)
