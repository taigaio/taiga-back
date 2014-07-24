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

import uuid

from django.db.models.loading import get_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout, login, authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework.response import Response
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from djmail.template_mail import MagicMailBuilder

from taiga.base.decorators import list_route, detail_route
from taiga.base.decorators import action
from taiga.base import exceptions as exc
from taiga.base.api import ModelCrudViewSet
from taiga.base.api import ModelListViewSet
from taiga.projects.votes import services as votes_service
from taiga.projects.serializers import StarredSerializer

from . import models
from . import serializers
from . import permissions


class MembersFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        project_id = request.QUERY_PARAMS.get('project', None)
        if project_id:
            Project = get_model('projects', 'Project')
            project = get_object_or_404(Project, pk=project_id)
            if project.memberships.filter(user=request.user).exists() or project.owner ==request.user:
                return queryset.filter(Q(memberships__project=project) | Q(id=project.owner.id)).distinct()
            else:
                raise exc.PermissionDenied(_("You don't have permisions to see this project users."))
        else:
            if request.user.is_superuser:
                return queryset
            else:
                return queryset.filter(pk=request.user.id)


class UsersViewSet(ModelCrudViewSet):
    permission_classes = (permissions.UserPermission,)
    serializer_class = serializers.UserSerializer
    queryset = models.User.objects.all()

    def pre_conditions_on_save(self, obj):
        if self.request.user.is_superuser:
            return

        if obj.id == self.request.user.id:
            return

        if obj.id is None:
            return

        raise exc.PreconditionError()

    def pre_conditions_on_delete(self, obj):
        if self.request.user.is_superuser:
            return

        if obj.id == self.request.user.id:
            return

        raise exc.PreconditionError()

    @list_route(methods=["POST"])
    def password_recovery(self, request, pk=None):
        username_or_email = request.DATA.get('username', None)

        self.check_permissions(request, "password_recovery", None)

        if not username_or_email:
            raise exc.WrongArguments(_("Invalid username or email"))

        try:
            queryset = models.User.objects.all()
            user = queryset.get(Q(username=username_or_email) |
                                    Q(email=username_or_email))
        except models.User.DoesNotExist:
            raise exc.WrongArguments(_("Invalid username or email"))

        user.token = str(uuid.uuid1())
        user.save(update_fields=["token"])

        mbuilder = MagicMailBuilder()
        email = mbuilder.password_recovery(user.email, {"user": user})
        email.send()

        return Response({"detail": _("Mail sended successful!"),
                         "email": user.email})

    @list_route(methods=["POST"])
    def change_password_from_recovery(self, request, pk=None):
        """
        Change password with token (from password recovery step).
        """

        self.check_permissions(request, "change_password_from_recovery", None)

        serializer = serializers.RecoverySerializer(data=request.DATA, many=False)
        if not serializer.is_valid():
            raise exc.WrongArguments(_("Token is invalid"))

        try:
            user = models.User.objects.get(token=serializer.data["token"])
        except models.User.DoesNotExist:
            raise exc.WrongArguments(_("Token is invalid"))

        user.set_password(serializer.data["password"])
        user.token = None
        user.save(update_fields=["password", "token"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=["POST"])
    def change_password(self, request, pk=None):
        """
        Change password to current logged user.
        """
        self.check_permissions(request, "change_password", None)

        password = request.DATA.get("password")

        if not password:
            raise exc.WrongArguments(_("Incomplete arguments"))

        if len(password) < 6:
            raise exc.WrongArguments(_("Invalid password length"))

        request.user.set_password(password)
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=["GET"])
    def starred(self, request, pk=None):
        user = self.get_object()
        self.check_permissions(request, 'starred', user)

        stars = votes_service.get_voted(user.pk, model=get_model('projects', 'Project'))
        stars_data = StarredSerializer(stars, many=True)
        return Response(stars_data.data)
