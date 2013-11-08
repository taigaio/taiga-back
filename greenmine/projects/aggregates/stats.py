# -*- coding: utf-8 -*-

from django.db.models import Q, Count


def _get_milestones_stats_for_backlog(project):
    """
    Get collection of stats for each millestone of project.
    Data returned by this function are used on backlog.
    """
    current_evolution = 0
    current_team_increment = 0
    current_client_increment = 0
    optimal_points_per_sprint = project.total_story_points / (project.total_milestones)
    future_team_increment = sum(project.future_team_increment.values())
    future_client_increment = sum(project.future_client_increment.values())

    milestones = project.milestones.order_by('estimated_start')

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
                    if current_evolution is not None else None)
    yield {
        'name': 'Project End',
        'optimal': optimal_points,
        'evolution': evolution,
        'team-increment': team_increment,
        'client-increment': client_increment,
    }


def _get_issues_assigned_to_counter(issues):
    issues_per_assigned_to = _get_issues_counter_per_field(issues, "assigned_to")
    if None in issues_per_assigned_to:
        del issues_per_assigned_to[None]

    issues_per_assigned_to["Unassigned"] = issues.count() - sum(issues_per_assigned_to.values())
    return issues_per_assigned_to


def _get_issues_counter_per_field(issues, field):
    return dict(
        map(
            lambda x: (x[field], x[field+'__count']),
            issues.values(field).order_by().annotate(Count(field))
        )
    )


def get_stats_for_project_issues(project):
    queryset = project.issues.all()
    project_issues_stats = {
        'total_issues': queryset.count(),
        'issues_per_type': _get_issues_counter_per_field(queryset, "type__name"),
        'issues_per_status': _get_issues_counter_per_field(queryset, "status__name"),
        'issues_per_priority': _get_issues_counter_per_field(queryset, "priority__name"),
        'issues_per_severity': _get_issues_counter_per_field(queryset, "severity__name"),
        'issues_per_owner': _get_issues_counter_per_field(queryset, "owner"),
        'issues_per_assigned_to': _get_issues_assigned_to_counter(queryset),
    }
    return project_issues_stats


def get_stats_for_project(project):
    project_stats = {
        'name': project.name,
        'total_milestones': project.total_milestones,
        'total_points': project.total_story_points,
        'closed_points': sum(project.closed_points.values()),
        'defined_points': sum(project.defined_points.values()),
        'assigned_points': sum(project.assigned_points.values()),
        'milestones': _get_milestones_stats_for_backlog(project)
    }
    return project_stats
