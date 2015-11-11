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

from django.utils.translation import ugettext as _
from django.db.models import Q, Count
from django.apps import apps
import datetime
import copy
import collections

from taiga.projects.history.models import HistoryEntry
from taiga.projects.userstories.models import RolePoints

def _count_status_object(status_obj, counting_storage):
    if status_obj.id in counting_storage:
        counting_storage[status_obj.id]['count'] += 1
    else:
        counting_storage[status_obj.id] = {}
        counting_storage[status_obj.id]['count'] = 1
        counting_storage[status_obj.id]['name'] = status_obj.name
        counting_storage[status_obj.id]['id'] = status_obj.id
        counting_storage[status_obj.id]['color'] = status_obj.color


def _count_owned_object(user_obj, counting_storage):
    if user_obj:
        if user_obj.id in counting_storage:
            counting_storage[user_obj.id]['count'] += 1
        else:
            counting_storage[user_obj.id] = {}
            counting_storage[user_obj.id]['count'] = 1
            counting_storage[user_obj.id]['username'] = user_obj.username
            counting_storage[user_obj.id]['name'] = user_obj.get_full_name()
            counting_storage[user_obj.id]['id'] = user_obj.id
            counting_storage[user_obj.id]['color'] = user_obj.color
    else:
        if 0 in counting_storage:
            counting_storage[0]['count'] += 1
        else:
            counting_storage[0] = {}
            counting_storage[0]['count'] = 1
            counting_storage[0]['username'] = _('Unassigned')
            counting_storage[0]['name'] = _('Unassigned')
            counting_storage[0]['id'] = 0
            counting_storage[0]['color'] = 'black'


def get_stats_for_project_issues(project):
    project_issues_stats = {
        'total_issues': 0,
        'opened_issues': 0,
        'closed_issues': 0,
        'issues_per_type': {},
        'issues_per_status': {},
        'issues_per_priority': {},
        'issues_per_severity': {},
        'issues_per_owner': {},
        'issues_per_assigned_to': {},
        'last_four_weeks_days': {
            'by_open_closed': {'open': [], 'closed': []},
            'by_severity': {},
            'by_priority': {},
            'by_status': {},
        }

    }

    issues = project.issues.all().select_related(
        'status', 'priority', 'type', 'severity', 'owner', 'assigned_to'
    )
    for issue in issues:
        project_issues_stats['total_issues'] += 1
        if issue.status.is_closed:
            project_issues_stats['closed_issues'] += 1
        else:
            project_issues_stats['opened_issues'] += 1
        _count_status_object(issue.type, project_issues_stats['issues_per_type'])
        _count_status_object(issue.status, project_issues_stats['issues_per_status'])
        _count_status_object(issue.priority, project_issues_stats['issues_per_priority'])
        _count_status_object(issue.severity, project_issues_stats['issues_per_severity'])
        _count_owned_object(issue.owner, project_issues_stats['issues_per_owner'])
        _count_owned_object(issue.assigned_to, project_issues_stats['issues_per_assigned_to'])

    for severity in project_issues_stats['issues_per_severity'].values():
        project_issues_stats['last_four_weeks_days']['by_severity'][severity['id']] = copy.copy(severity)
        del(project_issues_stats['last_four_weeks_days']['by_severity'][severity['id']]['count'])
        project_issues_stats['last_four_weeks_days']['by_severity'][severity['id']]['data'] = []

    for priority in project_issues_stats['issues_per_priority'].values():
        project_issues_stats['last_four_weeks_days']['by_priority'][priority['id']] = copy.copy(priority)
        del(project_issues_stats['last_four_weeks_days']['by_priority'][priority['id']]['count'])
        project_issues_stats['last_four_weeks_days']['by_priority'][priority['id']]['data'] = []

    for x in range(27, -1, -1):
        day = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0)) - datetime.timedelta(days=x)
        next_day = day + datetime.timedelta(days=1)

        open_this_day = filter(lambda x: x.created_date.replace(tzinfo=None) >= day, issues)
        open_this_day = filter(lambda x: x.created_date.replace(tzinfo=None) < next_day, open_this_day)
        open_this_day = len(list(open_this_day))
        project_issues_stats['last_four_weeks_days']['by_open_closed']['open'].append(open_this_day)

        closed_this_day = filter(lambda x: x.finished_date, issues)
        closed_this_day = filter(lambda x: x.finished_date.replace(tzinfo=None) >= day, closed_this_day)
        closed_this_day = filter(lambda x: x.finished_date.replace(tzinfo=None) < next_day, closed_this_day)
        closed_this_day = len(list(closed_this_day))
        project_issues_stats['last_four_weeks_days']['by_open_closed']['closed'].append(closed_this_day)

        opened_this_day = filter(lambda x: x.created_date.replace(tzinfo=None) < next_day, issues)
        opened_this_day = list(filter(lambda x: x.finished_date is None or x.finished_date.replace(tzinfo=None) > day, opened_this_day))

        for severity in project_issues_stats['last_four_weeks_days']['by_severity']:
            by_severity = filter(lambda x: x.severity_id == severity, opened_this_day)
            by_severity = len(list(by_severity))
            project_issues_stats['last_four_weeks_days']['by_severity'][severity]['data'].append(by_severity)

        for priority in project_issues_stats['last_four_weeks_days']['by_priority']:
            by_priority = filter(lambda x: x.priority_id == priority, opened_this_day)
            by_priority = len(list(by_priority))
            project_issues_stats['last_four_weeks_days']['by_priority'][priority]['data'].append(by_priority)

    return project_issues_stats


def _get_milestones_stats_for_backlog(project, milestones):
    """
    Calculates the stats associated to the milestones parameter.

    - project is a Project model instance
        We assume this object have also the following numeric attributes:
        - _defined_points
        - _future_team_increment
        - _future_client_increment

    - milestones is a sorted dict of Milestone model instances sorted by estimated_start.
        We assume this objects have also the following numeric attributes:
        - _closed_points
        - _team_increment_points
        - _client_increment_points

    The returned result is a list of dicts where each entry contains the following keys:
        - name
        - optimal
        - evolution
        - team
        - client
    """
    current_evolution = 0
    current_team_increment = 0
    current_client_increment = 0
    optimal_points_per_sprint = 0
    optimal_points = 0
    team_increment = 0
    client_increment = 0

    total_story_points = project.total_story_points\
        if project.total_story_points not in [None, 0] else project._defined_points

    total_milestones = project.total_milestones\
        if project.total_milestones not in [None, 0] else len(milestones)

    if total_story_points and total_milestones:
        optimal_points_per_sprint = total_story_points / total_milestones

    milestones_count = len(milestones)
    milestones_stats = []
    for current_milestone_pos in range(0, max(milestones_count, total_milestones)):
        optimal_points = (total_story_points -
                            (optimal_points_per_sprint * current_milestone_pos))

        evolution = (total_story_points - current_evolution
                        if current_evolution is not None else None)

        if current_milestone_pos < milestones_count:
            current_milestone = list(milestones.values())[current_milestone_pos]
            milestone_name = current_milestone.name
            team_increment = current_team_increment
            client_increment = current_client_increment
            current_evolution += current_milestone._closed_points
            current_team_increment += current_milestone._team_increment_points
            current_client_increment += current_milestone._client_increment_points

        else:
            milestone_name = _("Future sprint")
            team_increment = current_team_increment + project._future_team_increment,
            client_increment = current_client_increment + project._future_client_increment,
            current_evolution = None

        milestones_stats.append({
            'name': milestone_name,
            'optimal': optimal_points,
            'evolution': evolution,
            'team-increment': team_increment,
            'client-increment': client_increment,
        })

    optimal_points -= optimal_points_per_sprint
    evolution = (total_story_points - current_evolution
                    if current_evolution is not None and total_story_points else None)

    milestones_stats.append({
        'name': _('Project End'),
        'optimal': optimal_points,
        'evolution': evolution,
        'team-increment': team_increment,
        'client-increment': client_increment,
    })

    return milestones_stats


def get_stats_for_project(project):
    # Let's fetch all the estimations related to a project with all the necesary
    # related data
    role_points = RolePoints.objects.filter(
        user_story__project = project,
    ).prefetch_related(
        "user_story",
        "user_story__assigned_to",
        "user_story__milestone",
        "user_story__status",
        "role",
        "points")

    # Data inicialization
    project._closed_points = 0
    project._closed_points_per_role = {}
    project._closed_points_from_closed_milestones = 0
    project._defined_points = 0
    project._defined_points_per_role = {}
    project._assigned_points = 0
    project._assigned_points_per_role = {}
    project._future_team_increment = 0
    project._future_client_increment = 0

    # The key will be the milestone id and it will be ordered by estimated_start
    milestones = collections.OrderedDict()
    for milestone in project.milestones.order_by("estimated_start"):
        milestone._closed_points = 0
        milestone._team_increment_points = 0
        milestone._client_increment_points = 0
        milestones[milestone.id] = milestone

    def _find_milestone_for_userstory(user_story):
        for m in milestones.values():
            if m.estimated_finish > user_story.created_date.date() and\
               m.estimated_start <= user_story.created_date.date():

              return m

        return None

    def _update_team_increment(milestone, value):
        if milestone:
            milestones[milestone.id]._team_increment_points += value
        else:
            project._future_team_increment += value

    def _update_client_increment(milestone, value):
        if milestone:
            milestones[milestone.id]._client_increment_points += value
        else:
            project._future_client_increment += value

    # Iterate over all the project estimations and update our stats
    for role_point in role_points:
        role_id = role_point.role.id
        points_value = role_point.points.value
        milestone = role_point.user_story.milestone
        is_team_requirement = role_point.user_story.team_requirement
        is_client_requirement = role_point.user_story.client_requirement
        us_milestone = _find_milestone_for_userstory(role_point.user_story)

        # None estimations doesn't affect to project stats
        if points_value is None:
            continue

        # Total defined points
        project._defined_points += points_value

        # Defined points per role
        project._defined_points_for_role = project._defined_points_per_role.get(role_id, 0)
        project._defined_points_for_role += points_value
        project._defined_points_per_role[role_id] = project._defined_points_for_role

        # Closed points
        if role_point.user_story.is_closed:
            project._closed_points += points_value
            closed_points_for_role = project._closed_points_per_role.get(role_id, 0)
            closed_points_for_role += points_value
            project._closed_points_per_role[role_id] = closed_points_for_role

            if milestone is not None:
                milestones[milestone.id]._closed_points += points_value

        if milestone is not None and milestone.closed:
            project._closed_points_from_closed_milestones += points_value

        # Assigned to milestone points
        if role_point.user_story.milestone is not None:
            project._assigned_points += points_value
            assigned_points_for_role = project._assigned_points_per_role.get(role_id, 0)
            assigned_points_for_role += points_value
            project._assigned_points_per_role[role_id] = assigned_points_for_role

        # Extra requirements
        if is_team_requirement and is_client_requirement:
            _update_team_increment(us_milestone, points_value/2)
            _update_client_increment(us_milestone, points_value/2)

        if is_team_requirement and not is_client_requirement:
            _update_team_increment(us_milestone, points_value)

        if not is_team_requirement and is_client_requirement:
            _update_client_increment(us_milestone, points_value)

    # Speed calculations
    speed = 0
    closed_milestones = len([m for m in milestones.values() if m.closed])
    if closed_milestones != 0:
        speed = project._closed_points_from_closed_milestones / closed_milestones

    milestones_stats = _get_milestones_stats_for_backlog(project, milestones)

    project_stats = {
        'name': project.name,
        'total_milestones': project.total_milestones,
        'total_points': project.total_story_points,
        'closed_points': project._closed_points,
        'closed_points_per_role': project._closed_points_per_role,
        'defined_points': project._defined_points,
        'defined_points_per_role': project._defined_points_per_role,
        'assigned_points': project._assigned_points,
        'assigned_points_per_role': project._assigned_points_per_role,
        'milestones': milestones_stats,
        'speed': speed,
    }
    return project_stats


def _get_closed_bugs_per_member_stats(project):
    # Closed bugs per user
    closed_bugs = project.issues.filter(status__is_closed=True)\
        .values('assigned_to')\
        .annotate(count=Count('assigned_to'))\
        .order_by()
    closed_bugs = { p["assigned_to"]: p["count"] for p in closed_bugs}
    return closed_bugs


def _get_iocaine_tasks_per_member_stats(project):
    # Iocaine tasks assigned per user
    iocaine_tasks = project.tasks.filter(is_iocaine=True)\
        .values('assigned_to')\
        .annotate(count=Count('assigned_to'))\
        .order_by()
    iocaine_tasks = { t["assigned_to"]: t["count"] for t in iocaine_tasks}
    return iocaine_tasks


def _get_wiki_changes_per_member_stats(project):
    # Wiki changes
    wiki_changes = {}
    wiki_page_keys = ["wiki.wikipage:%s"%id for id in project.wiki_pages.values_list("id", flat=True)]
    history_entries = HistoryEntry.objects.filter(key__in=wiki_page_keys).values('user')
    for entry in history_entries:
        editions = wiki_changes.get(entry["user"]["pk"], 0)
        wiki_changes[entry["user"]["pk"]] = editions + 1

    return wiki_changes


def _get_created_bugs_per_member_stats(project):
    # Created_bugs
    created_bugs = project.issues\
        .values('owner')\
        .annotate(count=Count('owner'))\
        .order_by()
    created_bugs = { p["owner"]: p["count"] for p in created_bugs }
    return created_bugs


def _get_closed_tasks_per_member_stats(project):
    # Closed tasks
    closed_tasks = project.tasks.filter(status__is_closed=True)\
        .values('assigned_to')\
        .annotate(count=Count('assigned_to'))\
        .order_by()
    closed_tasks = {p["assigned_to"]: p["count"] for p in closed_tasks}
    return closed_tasks


def get_member_stats_for_project(project):
    base_counters = {id: 0 for id in project.members.values_list("id", flat=True)}
    closed_bugs = base_counters.copy()
    closed_bugs.update(_get_closed_bugs_per_member_stats(project))
    iocaine_tasks = base_counters.copy()
    iocaine_tasks.update(_get_iocaine_tasks_per_member_stats(project))
    wiki_changes = base_counters.copy()
    wiki_changes.update(_get_wiki_changes_per_member_stats(project))
    created_bugs = base_counters.copy()
    created_bugs.update(_get_created_bugs_per_member_stats(project))
    closed_tasks = base_counters.copy()
    closed_tasks.update(_get_closed_tasks_per_member_stats(project))

    member_stats = {
        "closed_bugs": closed_bugs,
        "iocaine_tasks": iocaine_tasks,
        "wiki_changes": wiki_changes,
        "created_bugs": created_bugs,
        "closed_tasks": closed_tasks,
    }
    return member_stats
