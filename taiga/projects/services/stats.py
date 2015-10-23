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

from taiga.projects.history.models import HistoryEntry


def _get_total_story_points(project):
    return (project.total_story_points if project.total_story_points not in [None, 0] else
                    sum(project.calculated_points["defined"].values()))

def _get_total_milestones(project):
    return (project.total_milestones if project.total_milestones not in [None, 0] else
                    project.milestones.count())

def _get_milestones_stats_for_backlog(project):
    """
    Get collection of stats for each millestone of project.
    Data returned by this function are used on backlog.
    """
    current_evolution = 0
    current_team_increment = 0
    current_client_increment = 0

    optimal_points_per_sprint = 0

    total_story_points = _get_total_story_points(project)
    total_milestones = _get_total_milestones(project)

    if total_story_points and total_milestones:
        optimal_points_per_sprint = total_story_points / total_milestones

    future_team_increment = sum(project.future_team_increment.values())
    future_client_increment = sum(project.future_client_increment.values())

    milestones = project.milestones.order_by('estimated_start').\
            prefetch_related("user_stories",
                             "user_stories__role_points",
                             "user_stories__role_points__points")

    milestones = list(milestones)
    milestones_count = len(milestones)
    optimal_points = 0
    team_increment = 0
    client_increment = 0

    for current_milestone in range(0, max(milestones_count, total_milestones)):
        optimal_points = (total_story_points -
                            (optimal_points_per_sprint * current_milestone))

        evolution = (total_story_points - current_evolution
                        if current_evolution is not None else None)

        if current_milestone < milestones_count:
            ml = milestones[current_milestone]

            milestone_name = ml.name
            team_increment = current_team_increment
            client_increment = current_client_increment

            current_evolution += sum(ml.closed_points.values())
            current_team_increment += sum(ml.team_increment_points.values())
            current_client_increment += sum(ml.client_increment_points.values())

        else:
            milestone_name = _("Future sprint")
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
    evolution = (total_story_points - current_evolution
                    if current_evolution is not None and total_story_points else None)
    yield {
        'name': _('Project End'),
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


def get_stats_for_project(project):
    project = apps.get_model("projects", "Project").objects.\
        prefetch_related("milestones",
                                     "user_stories").\
        get(id=project.id)

    points = project.calculated_points
    closed_points = sum(points["closed"].values())
    closed_milestones = project.milestones.filter(closed=True).count()
    speed = 0
    if closed_milestones != 0:
        speed = closed_points / closed_milestones

    project_stats = {
        'name': project.name,
        'total_milestones': project.total_milestones,
        'total_points': project.total_story_points,
        'closed_points': closed_points,
        'closed_points_per_role': points["closed"],
        'defined_points': sum(points["defined"].values()),
        'defined_points_per_role': points["defined"],
        'assigned_points': sum(points["assigned"].values()),
        'assigned_points_per_role': points["assigned"],
        'milestones': _get_milestones_stats_for_backlog(project),
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
