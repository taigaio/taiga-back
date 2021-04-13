# -*- coding: utf-8 -*-
from taiga.base import status
from taiga.base.api.mixins import CreateModelMixin, BlockedByProjectMixin
from taiga.base.api.viewsets import GenericViewSet

from . import models
from . import permissions
from . import services
from . import validators

from django.conf import settings


class ContactViewSet(BlockedByProjectMixin, CreateModelMixin, GenericViewSet):
    permission_classes = (permissions.ContactPermission,)
    validator_class = validators.ContactEntryValidator
    model = models.ContactEntry

    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            if settings.CELERY_ENABLED:
                services.send_contact_email.delay(self.object.id)
            else:
                services.send_contact_email(self.object.id)

        return response

    def pre_save(self, obj):
        obj.user = self.request.user
        super().pre_save(obj)
