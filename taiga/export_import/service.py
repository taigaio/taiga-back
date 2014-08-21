from . import serializers
from taiga.projects.models import Project
from django.db.models import signals
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

def project_to_dict(project):
    return serializers.ProjectExportSerializer(project).data

def dict_to_project(data, owner=None):
    signals.pre_save.receivers = []
    signals.post_save.receivers = []
    signals.pre_delete.receivers = []
    signals.post_delete.receivers = []

    @transaction.atomic
    def store_project(data):
        project_data = {}
        for key, value in data.items():
            excluded_fields = [
                "default_points", "default_us_status", "default_task_status",
                "default_priority", "default_severity", "default_issue_status",
                "default_issue_type", "memberships", "points", "us_statuses",
                "task_statuses", "issue_statuses", "priorities", "severities",
                "issue_types", "roles", "milestones", "wiki_pages",
                "wiki_links", "notify_policies", "user_stories", "issues"
            ]
            if key not in excluded_fields:
                project_data[key] = value

        serialized = serializers.ProjectExportSerializer(data=project_data)
        serialized.is_valid()
        serialized.object._importing = True
        serialized.object.save()
        return serialized.object

    @transaction.atomic
    def store_choices(project, data, field, relation, serializer, default_field):
        relation.all().delete()

        for point in data[field]:
            serialized = serializer(data=point)
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

    @transaction.atomic
    def store_default_choices(project, data):
        project.default_points = project.points.all().get(name=data['default_points'])
        project.default_issue_type = project.issue_types.get(name=data['default_issue_type'])
        project.default_issue_status = project.issue_statuses.get(name=data['default_issue_status'])
        project.default_us_status = project.us_statuses.get(name=data['default_us_status'])
        project.default_task_status = project.task_statuses.get(name=data['default_task_status'])
        project.default_priority = project.priorities.get(name=data['default_priority'])
        project.default_severity = project.severities.get(name=data['default_severity'])
        project._importing = True
        project.save()

    @transaction.atomic
    def store_roles(project, data):
        project.roles.all().delete()
        for role in data['roles']:
            serialized = serializers.RoleExportSerializer(data=role)
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

    @transaction.atomic
    def store_memberships(project, data):
        for membership in data['memberships']:
            serialized = serializers.MembershipExportSerializer(data=membership, context={"project": project})
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

    @transaction.atomic
    def store_task(project, us, task):
        serialized = serializers.TaskExportSerializer(data=task, context={"project": project})
        serialized.is_valid()
        serialized.object.user_story = us
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

        for task_attachment in task['attachments']:
            store_attachment(project, serialized.object, task_attachment)

    @transaction.atomic
    def store_milestones(project, data):
        for milestone in data['milestones']:
            serialized = serializers.MilestoneExportSerializer(data=milestone)
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

            for task_without_us in milestone['tasks_without_us']:
                store_task(project, None, task_without_us)

    def store_attachment(project, obj, attachment):
        serialized = serializers.AttachmentExportSerializer(data=attachment)
        serialized.is_valid()
        serialized.object.content_type = ContentType.objects.get_for_model(obj.__class__)
        serialized.object.object_id = obj.id
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

    @transaction.atomic
    def store_wiki_pages(project, data):
        for wiki_page in data['wiki_pages']:
            serialized = serializers.WikiPageExportSerializer(data=wiki_page)
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

            for attachment in wiki_page['attachments']:
                store_attachment(project, serialized.object, attachment)

    @transaction.atomic
    def store_wiki_links(project, data):
        for wiki_link in data['wiki_links']:
            serialized = serializers.WikiLinkExportSerializer(data=wiki_link)
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

    @transaction.atomic
    def store_role_point(project, us, role_point):
        serialized = serializers.RolePointsExportSerializer(data=role_point, context={"project": project} )
        serialized.is_valid()
        serialized.object.user_story = us
        serialized.save()

    @transaction.atomic
    def store_user_stories(project, data):
        for userstory in data['user_stories']:
            userstory_data = {}
            for key, value in userstory.items():
                excluded_fields = [
                    'tasks', 'role_points'
                ]
                if key not in excluded_fields:
                    userstory_data[key] = value
            serialized_us = serializers.UserStoryExportSerializer(data=userstory_data, context={"project": project})
            serialized_us.is_valid()
            serialized_us.object.project = project
            serialized_us.object._importing = True
            serialized_us.save()

            for task in userstory['tasks']:
                store_task(project, serialized_us.object, task)

            for us_attachment in userstory['attachments']:
                store_attachment(project, serialized_us.object, us_attachment)

            for role_point in userstory['role_points']:
                store_role_point(project, serialized_us.object, role_point)

    @transaction.atomic
    def store_issues(project, data):
        for issue in data['issues']:
            serialized = serializers.IssueExportSerializer(data=issue, context={"project": project})
            serialized.is_valid()
            serialized.object.project = project
            serialized.object._importing = True
            serialized.save()

            for attachment in issue['attachments']:
                store_attachment(project, serialized.object, attachment)

    if owner:
        data['owner'] = owner

    project = store_project(data)
    store_choices(project, data, "points", project.points, serializers.PointsExportSerializer, "default_points")
    store_choices(project, data, "issue_types", project.issue_types, serializers.IssueTypeExportSerializer, "default_issue_type")
    store_choices(project, data, "issue_statuses", project.issue_statuses, serializers.IssueStatusExportSerializer, "default_issue_status")
    store_choices(project, data, "us_statuses", project.us_statuses, serializers.UserStoryStatusExportSerializer, "default_us_status")
    store_choices(project, data, "task_statuses", project.task_statuses, serializers.TaskStatusExportSerializer, "default_task_status")
    store_choices(project, data, "priorities", project.priorities, serializers.PriorityExportSerializer, "default_priority")
    store_choices(project, data, "severities", project.severities, serializers.SeverityExportSerializer, "default_severity")
    store_default_choices(project, data)
    store_roles(project, data)
    store_memberships(project, data)
    store_milestones(project, data)
    store_wiki_pages(project, data)
    store_wiki_links(project, data)

    store_user_stories(project, data)
    store_issues(project, data)
