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

from django.apps import apps
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings

from easy_thumbnails.source_generators import pil_image


from rest_framework.response import Response
from rest_framework.filters import BaseFilterBackend
from rest_framework import status

from djmail.template_mail import MagicMailBuilder

from taiga.auth.tokens import get_user_for_token
from taiga.base.decorators import list_route, detail_route
from taiga.base import exceptions as exc
from taiga.base.api import ModelCrudViewSet
from taiga.base.utils.slug import slugify_uniquely
from taiga.projects.votes import services as votes_service
from taiga.projects.serializers import StarredSerializer

from . import models
from . import serializers
from . import permissions
from .signals import user_cancel_account as user_cancel_account_signal


class MembersFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        project_id = request.QUERY_PARAMS.get('project', None)
        if project_id:
            Project = apps.get_model('projects', 'Project')
            project = get_object_or_404(Project, pk=project_id)
            if request.user.is_authenticated() and (project.memberships.filter(user=request.user).exists() or project.owner == request.user):
                return queryset.filter(Q(memberships__project=project) | Q(id=project.owner.id)).distinct()
            else:
                raise exc.PermissionDenied(_("You don't have permisions to see this project users."))

        if request.user.is_superuser:
            return queryset

        return []


class UsersViewSet(ModelCrudViewSet):
    permission_classes = (permissions.UserPermission,)
    serializer_class = serializers.UserSerializer
    queryset = models.User.objects.all()

    def create(self, *args, **kwargs):
        raise exc.NotSupported()

    def list(self, request, *args, **kwargs):
        self.object_list = MembersFilterBackend().filter_queryset(request, self.get_queryset(), self)

        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        return Response(serializer.data)

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

        current_password = request.DATA.get("current_password")
        password = request.DATA.get("password")
        if not current_password:
            raise exc.WrongArguments(_("Current password parameter needed"))

        if not password:
            raise exc.WrongArguments(_("New password parameter needed"))

        if len(password) < 6:
            raise exc.WrongArguments(_("Invalid password length at least 6 charaters needed"))

        if not request.user.check_password(current_password):
            raise exc.WrongArguments(_("Invalid current password"))

        request.user.set_password(password)
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=["POST"])
    def change_avatar(self, request):
        """
        Change avatar to current logged user.
        """
        self.check_permissions(request, "change_avatar", None)

        avatar = request.FILES.get('avatar', None)

        if not avatar:
            raise exc.WrongArguments(_("Incomplete arguments"))

        try:
            pil_image(avatar)
        except Exception:
            raise exc.WrongArguments(_("Invalid image format"))

        request.user.photo = avatar
        request.user.save(update_fields=["photo"])
        user_data = serializers.UserSerializer(request.user).data

        return Response(user_data, status=status.HTTP_200_OK)

    @list_route(methods=["POST"])
    def remove_avatar(self, request):
        """
        Remove the avatar of current logged user.
        """
        self.check_permissions(request, "remove_avatar", None)
        request.user.photo = None
        request.user.save(update_fields=["photo"])
        user_data = serializers.UserSerializer(request.user).data
        return Response(user_data, status=status.HTTP_200_OK)

    @detail_route(methods=["GET"])
    def starred(self, request, pk=None):
        user = self.get_object()
        self.check_permissions(request, 'starred', user)

        stars = votes_service.get_voted(user.pk, model=apps.get_model('projects', 'Project'))
        stars_data = StarredSerializer(stars, many=True)
        return Response(stars_data.data)

    #TODO: commit_on_success
    def partial_update(self, request, *args, **kwargs):
        """
        We must detect if the user is trying to change his email so we can
        save that value and generate a token that allows him to validate it in
        the new email account
        """
        user = self.get_object()
        self.check_permissions(request, "update", user)

        ret = super(UsersViewSet, self).partial_update(request, *args, **kwargs)

        new_email = request.DATA.get('email', None)
        if new_email is not None:
            valid_new_email = True
            duplicated_email = models.User.objects.filter(email = new_email).exists()

            try:
                validate_email(new_email)
            except ValidationError:
                valid_new_email = False

            valid_new_email = valid_new_email and new_email != request.user.email

            if duplicated_email:
                raise exc.WrongArguments(_("Duplicated email"))
            elif not valid_new_email:
                raise exc.WrongArguments(_("Not valid email"))

            #We need to generate a token for the email
            request.user.email_token = str(uuid.uuid1())
            request.user.new_email = new_email
            request.user.save(update_fields=["email_token", "new_email"])
            mbuilder = MagicMailBuilder()
            email = mbuilder.change_email(request.user.new_email, {"user": request.user})
            email.send()

        return ret

    @list_route(methods=["POST"])
    def change_email(self, request, pk=None):
        """
        Verify the email change to current logged user.
        """
        serializer = serializers.ChangeEmailSerializer(data=request.DATA, many=False)
        if not serializer.is_valid():
            raise exc.WrongArguments(_("Invalid, are you sure the token is correct and you didn't use it before?"))

        try:
            user = models.User.objects.get(email_token=serializer.data["email_token"])
        except models.User.DoesNotExist:
            raise exc.WrongArguments(_("Invalid, are you sure the token is correct and you didn't use it before?"))

        self.check_permissions(request, "change_email", user)
        user.email = user.new_email
        user.new_email = None
        user.email_token = None
        user.save(update_fields=["email", "new_email", "email_token"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=["POST"])
    def cancel(self, request, pk=None):
        """
        Cancel an account via token
        """
        serializer = serializers.CancelAccountSerializer(data=request.DATA, many=False)
        if not serializer.is_valid():
            raise exc.WrongArguments(_("Invalid, are you sure the token is correct?"))

        try:
            max_age_cancel_account = getattr(settings, "MAX_AGE_CANCEL_ACCOUNT", None)
            user = get_user_for_token(serializer.data["cancel_token"], "cancel_account",
                max_age=max_age_cancel_account)

        except exc.NotAuthenticated:
            raise exc.WrongArguments(_("Invalid, are you sure the token is correct?"))

        if not user.is_active:
            raise exc.WrongArguments(_("Invalid, are you sure the token is correct?"))

        user.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        user = self.get_object()
        self.check_permissions(request, "destroy", user)
        stream = request.stream
        request_data = stream is not None and stream.GET or None
        user_cancel_account_signal.send(sender=user.__class__, user=user, request_data=request_data)
        user.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)
