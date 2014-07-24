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

from django.db.models import Q, Count
import datetime
import copy


def _get_milestones_stats_for_backlog(project):
    """
    Get collection of stats for each millestone of project.
    Data returned by this function are used on backlog.
    """
    current_evolution = 0
    current_team_increment = 0
    current_client_increment = 0

    optimal_points_per_sprint = 0
    if project.total_story_points and project.total_milestones:
        optimal_points_per_sprint = project.total_story_points / project.total_milestones

    future_team_increment = sum(project.future_team_increment.values())
    future_client_increment = sum(project.future_client_increment.values())

    milestones = project.milestones.order_by('estimated_start')

    optimal_points = 0
    team_increment = 0
    client_increment = 0
    for current_milestone in range(0, max(milestones.count(), project.total_milestones)):
        optimal_points = (project.total_story_points -
                            (optimal_points_per_sprint * current_milestone))

        evolution = (project.total_story_points - current_evolution
                        if current_evolution is not None else None)

        if current_milestone < milestones.count():
            ml = milestones[current_milestone]
            milestone_name = ml.name
            team_increment = current_team_increment
            client_increment = current_client_increment

            current_evolution += sum(ml.closed_points.values())
            current_team_increment += sum(ml.team_increment_points.values())
            current_client_increment += sum(ml.client_increment_points.values())
        else:
            milestone_name = "Future sprint"
            team_increment = current_team_increment + future_team_increment,
            client_increment = current_client_increment + future_client_increment,
            current_evolution = None

        yield {
            'name': milestone_name,
            'optimal': optimal_points,
            'evolution': evolution,
            'team-increment': team_increment,
            'client-increment': client_increment,
        }

    optimal_points -= optimal_points_per_sprint
    evolution = (project.total_story_points - current_evolution
                    if current_evolution is not None and project.total_story_points else None)
    yield {
        'name': 'Project End',
        'optimal': optimal_points,
        'evolution': evolution,
        'team-increment': team_increment,
        'client-increment': client_increment,
    }


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
            counting_storage[0]['username'] = 'Unassigned'
            counting_storage[0]['name'] = 'Unassigned'
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


def get_stats_for_project(project):
    project_stats = {
        'name': project.name,
        'total_milestones': project.total_milestones,
        'total_points': project.total_story_points,
        'closed_points': sum(project.closed_points.values()),
        'closed_points_per_role': project.closed_points,
        'defined_points': sum(project.defined_points.values()),
        'defined_points_per_role': project.defined_points,
        'assigned_points': sum(project.assigned_points.values()),
        'assigned_points_per_role': project.assigned_points,
        'milestones': _get_milestones_stats_for_backlog(project)
    }
    return project_stats
