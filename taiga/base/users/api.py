# -*- coding: utf-8 -*-

import uuid

from django.db.models.loading import get_model
from django.db.models import Q
from django.contrib.auth import logout, login, authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework.decorators import list_route, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, viewsets

from djmail.template_mail import MagicMailBuilder

from taiga.base import exceptions as exc
from taiga.base.filters import FilterBackend
from taiga.base.api import ModelCrudViewSet, RetrieveModelMixin

from .models import User, Role
from .serializers import UserSerializer, RecoverySerializer



class UsersViewSet(ModelCrudViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_fields = [("project", "memberships__project__pk")]

    def pre_conditions_on_save(self, obj):
        if not self.request.user.is_superuser and obj.id != self.request.user.id:
            raise exc.PreconditionError()

    def pre_conditions_on_delete(self, obj):
        if not self.request.user.is_superuser and obj.id != self.request.user.id:
            raise exc.PreconditionError()

    @list_route(permission_classes=[AllowAny], methods=["POST"])
    def password_recovery(self, request, pk=None):
        username_or_email = request.DATA.get('username', None)

        if not username_or_email:
            raise exc.WrongArguments(_("Invalid username or email"))

        try:
            queryset = User.objects.all()
            user = queryset.get(Q(username=username_or_email) |
                                    Q(email=username_or_email))
        except User.DoesNotExist:
            raise exc.WrongArguments(_("Invalid username or email"))

        user.token = str(uuid.uuid1())
        user.save(update_fields=["token"])

        mbuilder = MagicMailBuilder()
        email = mbuilder.password_recovery(user.email, {"user": user})
        email.send()

        return Response({"detail": _("Mail sended successful!")})

    @list_route(permission_classes=[AllowAny], methods=["POST"])
    def change_password_from_recovery(self, request, pk=None):
        """
        Change password with token (from password recovery step).
        """
        serializer = RecoverySerializer(data=request.DATA, many=False)
        if not serializer.is_valid():
            raise exc.WrongArguments(_("Token is invalid"))

        user = User.objects.get(token=serializer.data["token"])
        user.set_password(serializer.data["password"])
        user.token = None
        user.save(update_fields=["password", "token"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(permission_classes=[IsAuthenticated], methods=["POST"])
    def change_password(self, request, pk=None):
        """
        Change password to current logged user.
        """
        password = request.DATA.get("password")

        if not password:
            raise exc.WrongArguments(_("Incomplete arguments"))

        if len(password) < 6:
            raise exc.WrongArguments(_("Invalid password length"))

        request.user.set_password(password)
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)
