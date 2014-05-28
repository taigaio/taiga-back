from django.db.models import F
from django.db.transaction import atomic
from django.db.models.loading import get_model
from django.contrib.auth import get_user_model

from .models import Fan, Stars


def star(project, user):
    """Star a project for an user.

    If the user has already starred the project nothing happends so this function can be considered
    idempotent.

    :param project: :class:`~taiga.projects.models.Project` instance.
    :param user: :class:`~taiga.users.models.User` instance.
    """

    with atomic():
        fan, created = Fan.objects.get_or_create(project=project,
                                                 user=user)
        if not created:
            return

        stars, _ = Stars.objects.get_or_create(project=project)
        stars.count = F('count') + 1
        stars.save()


def unstar(project, user):
    """
    Unstar a project for an user.

    If the user has not starred the project nothing happens so this function can be considered
    idempotent.

    :param project: :class:`~taiga.projects.models.Project` instance.
    :param user: :class:`~taiga.users.models.User` instance.
    """

    with atomic():
        qs = Fan.objects.filter(project=project, user=user)
        if not qs.exists():
            return

        qs.delete()

        stars, _ = Stars.objects.get_or_create(project=project)
        stars.count = F('count') - 1
        stars.save()


def get_stars(project):
    """
    Get the count of stars a project have.
    """
    instance, _ = Stars.objects.get_or_create(project=project)
    return instance.count


def get_fans(project_or_id):
    """Get the fans a project have."""
    qs = get_user_model().objects.get_queryset()
    if isinstance(project_or_id, int):
        qs = qs.filter(fans__project_id=project_or_id)
    else:
        qs = qs.filter(fans__project=project_or_id)

    return qs


def get_starred(user_or_id):
    """Get the projects an user has starred."""
    project_model = get_model("projects", "Project")
    qs = project_model.objects.get_queryset()

    if isinstance(user_or_id, int):
        qs = qs.filter(fans__user_id=user_or_id)
    else:
        qs = qs.filter(fans__user=user_or_id)

    return qs


def attach_startscount_to_queryset(queryset):
    """
    Attach stars count to each object of projects queryset.

    Because of lazynes of starts objects creation, this makes
    much simple and more efficient way to access to project
    starts number.

    (The other way was be do it on serializer with some try/except
    blocks and additional queryes)
    """
    sql = ("SELECT coalesce(stars_stars.count, 0) FROM stars_stars "
           "WHERE stars_stars.project_id = projects_project.id ")
    qs = queryset.extra(select={"starts_count": sql})
    return qs

