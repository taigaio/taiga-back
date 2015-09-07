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

"""
This model contains a domain logic for users application.
"""

from django.apps import apps
from django.db.models import Q
from django.db import connection
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError

from taiga.base import exceptions as exc
from taiga.base.utils.urls import get_absolute_url
from taiga.projects.notifications.choices import NotifyLevel

from .gravatar import get_gravatar_url


def get_and_validate_user(*, username:str, password:str) -> bool:
    """
    Check if user with username/email exists and specified
    password matchs well with existing user password.

    if user is valid,  user is returned else, corresponding
    exception is raised.
    """

    user_model = apps.get_model("users", "User")
    qs = user_model.objects.filter(Q(username=username) |
                                   Q(email=username))
    if len(qs) == 0:
        raise exc.WrongArguments(_("Username or password does not matches user."))

    user = qs[0]
    if not user.check_password(password):
        raise exc.WrongArguments(_("Username or password does not matches user."))

    return user


def get_photo_url(photo):
    """Get a photo absolute url and the photo automatically cropped."""
    try:
        url = get_thumbnailer(photo)['avatar'].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None


def get_photo_or_gravatar_url(user):
    """Get the user's photo/gravatar url."""
    if user:
        return get_photo_url(user.photo) if user.photo else get_gravatar_url(user.email)
    return ""


def get_big_photo_url(photo):
    """Get a big photo absolute url and the photo automatically cropped."""
    try:
        url = get_thumbnailer(photo)['big-avatar'].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None


def get_big_photo_or_gravatar_url(user):
    """Get the user's big photo/gravatar url."""
    if not user:
        return ""

    if user.photo:
        return get_big_photo_url(user.photo)
    else:
        return get_gravatar_url(user.email, size=settings.DEFAULT_BIG_AVATAR_SIZE)


def get_visible_project_ids(from_user, by_user):
    """Calculate the project_ids from one user visible by another"""
    required_permissions = ["view_project"]
    #Or condition for membership filtering, the basic one is the access to projects allowing anonymous visualization
    member_perm_conditions = Q(project__anon_permissions__contains=required_permissions)

    # Authenticated
    if by_user.is_authenticated():
        #Calculating the projects wich from_user user is member
        by_user_project_ids = by_user.memberships.values_list("project__id", flat=True)
        #Adding to the condition two OR situations:
        #- The from user has a role that allows access to the project
        #- The to user is the owner
        member_perm_conditions |= \
            Q(project__id__in=by_user_project_ids, role__permissions__contains=required_permissions) |\
            Q(project__id__in=by_user_project_ids, is_owner=True)

    Membership = apps.get_model('projects', 'Membership')
    #Calculating the user memberships adding the permission filter for the by user
    memberships_qs = Membership.objects.filter(member_perm_conditions, user=from_user)
    project_ids = memberships_qs.values_list("project__id", flat=True)
    return project_ids


def get_stats_for_user(from_user, by_user):
    """Get the user stats"""
    project_ids = get_visible_project_ids(from_user, by_user)

    total_num_projects = len(project_ids)

    roles = [_(r) for r in from_user.memberships.filter(project__id__in=project_ids).values_list("role__name", flat=True)]
    roles = list(set(roles))

    User = apps.get_model('users', 'User')
    total_num_contacts = User.objects.filter(memberships__project__id__in=project_ids)\
        .exclude(id=from_user.id)\
        .distinct()\
        .count()

    UserStory = apps.get_model('userstories', 'UserStory')
    total_num_closed_userstories = UserStory.objects.filter(
        is_closed=True,
        project__id__in=project_ids,
        assigned_to=from_user).count()

    project_stats = {
        'total_num_projects': total_num_projects,
        'roles': roles,
        'total_num_contacts': total_num_contacts,
        'total_num_closed_userstories': total_num_closed_userstories,
    }
    return project_stats


def get_voted_content_for_user(user):
    """Returns a dict where:
        - The key is the content_type model
        - The values are list of id's of the different objects voted by the user
    """
    if user.is_anonymous():
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
    if user.is_anonymous():
        return {}

    user_watches = {}
    for (ct_model, object_id) in user.watched.values_list("content_type__model", "object_id"):
        list = user_watches.get(ct_model, [])
        list.append(object_id)
        user_watches[ct_model] = list

    return user_watches


def _build_favourites_sql_for_projects(for_user):
    sql = """
	SELECT projects_project.id AS id, null AS ref, 'project' AS type, 'watch' AS action,
        tags, notifications_notifypolicy.project_id AS object_id, projects_project.id AS project,
        slug AS slug, projects_project.name AS subject,
        notifications_notifypolicy.created_at, coalesce(watchers, 0) as total_watchers, coalesce(votes_votes.count, 0) total_votes, null AS assigned_to
	    FROM notifications_notifypolicy
	    INNER JOIN projects_project
		      ON (projects_project.id = notifications_notifypolicy.project_id)
	    LEFT JOIN (SELECT project_id, count(*) watchers
                   FROM notifications_notifypolicy
                   WHERE notifications_notifypolicy.notify_level != {ignore_notify_level}
                   GROUP BY project_id
                ) type_watchers
		      ON projects_project.id = type_watchers.project_id
	    LEFT JOIN votes_votes
		      ON (projects_project.id = votes_votes.object_id AND {project_content_type_id} = votes_votes.content_type_id)
	    WHERE notifications_notifypolicy.user_id = {for_user_id}
	UNION
	SELECT projects_project.id AS id, null AS ref, 'project' AS type, 'vote' AS action,
        tags, votes_vote.object_id AS object_id, projects_project.id AS project,
        slug AS slug, projects_project.name AS subject,
        votes_vote.created_date, coalesce(watchers, 0) as total_watchers, coalesce(votes_votes.count, 0) total_votes, null AS assigned_to
	    FROM votes_vote
	    INNER JOIN projects_project
		      ON (projects_project.id = votes_vote.object_id)
	    LEFT JOIN (SELECT project_id, count(*) watchers
                   FROM notifications_notifypolicy
                   WHERE notifications_notifypolicy.notify_level != {ignore_notify_level}
                   GROUP BY project_id
                ) type_watchers
		      ON projects_project.id = type_watchers.project_id
        LEFT JOIN votes_votes
		      ON (projects_project.id = votes_votes.object_id AND {project_content_type_id} = votes_votes.content_type_id)
	    WHERE votes_vote.user_id = {for_user_id}
    """
    sql = sql.format(
        for_user_id=for_user.id,
        ignore_notify_level=NotifyLevel.ignore,
        project_content_type_id=ContentType.objects.get(app_label="projects", model="project").id)
    return sql



def _build_favourites_sql_for_type(for_user, type, table_name, ref_column="ref",
                              project_column="project_id", assigned_to_column="assigned_to_id",
                              slug_column="slug", subject_column="subject"):
    sql = """
	SELECT {table_name}.id AS id, {ref_column} AS ref, '{type}' AS type, 'watch' AS action,
        tags, notifications_watched.object_id AS object_id, {table_name}.{project_column} AS project,
        {slug_column} AS slug, {subject_column} AS subject,
        notifications_watched.created_date, coalesce(watchers, 0) as total_watchers, coalesce(votes_votes.count, 0) total_votes, {assigned_to_column}  AS assigned_to
	    FROM notifications_watched
	    INNER JOIN django_content_type
		      ON (notifications_watched.content_type_id = django_content_type.id AND django_content_type.model = '{type}')
	    INNER JOIN {table_name}
		      ON ({table_name}.id = notifications_watched.object_id)
	    LEFT JOIN (SELECT object_id, content_type_id, count(*) watchers FROM notifications_watched GROUP BY object_id, content_type_id) type_watchers
		      ON {table_name}.id = type_watchers.object_id AND django_content_type.id = type_watchers.content_type_id
	    LEFT JOIN votes_votes
		      ON ({table_name}.id = votes_votes.object_id AND django_content_type.id = votes_votes.content_type_id)
	    WHERE notifications_watched.user_id = {for_user_id}
	UNION
	SELECT {table_name}.id AS id, {ref_column} AS ref, '{type}' AS type, 'vote' AS action,
        tags, votes_vote.object_id AS object_id, {table_name}.{project_column} AS project,
        {slug_column} AS slug, {subject_column} AS subject,
        votes_vote.created_date, coalesce(watchers, 0) as total_watchers, votes_votes.count total_votes, {assigned_to_column}  AS assigned_to
	    FROM votes_vote
	    INNER JOIN django_content_type
		      ON (votes_vote.content_type_id = django_content_type.id AND django_content_type.model = '{type}')
	    INNER JOIN {table_name}
		      ON ({table_name}.id = votes_vote.object_id)
	    LEFT JOIN (SELECT object_id, content_type_id, count(*) watchers FROM notifications_watched GROUP BY object_id, content_type_id) type_watchers
		      ON {table_name}.id = type_watchers.object_id AND django_content_type.id = type_watchers.content_type_id
	    LEFT JOIN votes_votes
		      ON ({table_name}.id = votes_votes.object_id AND django_content_type.id = votes_votes.content_type_id)
	    WHERE votes_vote.user_id = {for_user_id}
    """
    sql = sql.format(for_user_id=for_user.id, type=type, table_name=table_name,
                      ref_column = ref_column, project_column=project_column,
                      assigned_to_column=assigned_to_column, slug_column=slug_column,
                      subject_column=subject_column)

    return sql


def get_favourites_list(for_user, from_user, type=None, action=None, q=None):
    filters_sql = ""
    and_needed = False

    if type:
        filters_sql += " AND type = '{type}' ".format(type=type)

    if action:
        filters_sql += " AND action = '{action}' ".format(action=action)

    if q:
        filters_sql += " AND to_tsvector(coalesce(subject, '')) @@ plainto_tsquery('{q}') ".format(q=q)

    sql = """
    -- BEGIN Basic info: we need to mix info from different tables and denormalize it
    SELECT entities.*,
           projects_project.name as project_name, projects_project.slug as project_slug, projects_project.is_private as project_is_private,
           users_user.username assigned_to_username, users_user.full_name assigned_to_full_name, users_user.photo assigned_to_photo, users_user.email assigned_to_email
        FROM (
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
                )
        ))
    -- END Permissions checking
        {filters_sql}

    ORDER BY entities.created_date;
    """

    from_user_id = -1
    if not from_user.is_anonymous():
        from_user_id = from_user.id

    sql = sql.format(
        for_user_id=for_user.id,
        from_user_id=from_user_id,
        filters_sql=filters_sql,
        userstories_sql=_build_favourites_sql_for_type(for_user, "userstory", "userstories_userstory", slug_column="null"),
        tasks_sql=_build_favourites_sql_for_type(for_user, "task", "tasks_task", slug_column="null"),
        issues_sql=_build_favourites_sql_for_type(for_user, "issue", "issues_issue", slug_column="null"),
        projects_sql=_build_favourites_sql_for_projects(for_user))

    cursor = connection.cursor()
    cursor.execute(sql)

    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
