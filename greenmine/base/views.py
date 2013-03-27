from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'projects': reverse('project-list', request=request, format=format),
        'milestones': reverse('milestone-list', request=request, format=format),
        'user-stories': reverse('user-story-list', request=request, format=format),
        'changes': reverse('change-list', request=request, format=format),
        'change-attachments': reverse('change-attachment-list', request=request, format=format),
        'tasks': reverse('task-list', request=request, format=format),
        'severities': reverse('severity-list', request=request, format=format),
        'issue-status': reverse('issue-status-list', request=request, format=format),
        'task-status': reverse('task-status-list', request=request, format=format),
        'user-story-status': reverse('user-story-status-list', request=request, format=format),
        'priorities': reverse('priority-list', request=request, format=format),
        'issue-types': reverse('issue-type-list', request=request, format=format),
        'points': reverse('points-list', request=request, format=format),
    })
