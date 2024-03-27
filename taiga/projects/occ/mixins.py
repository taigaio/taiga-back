# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.utils.translation import gettext_lazy as _

from taiga.base import exceptions as exc
from taiga.base.utils import db
from taiga.projects.history.services import get_modified_fields


class OCCResourceMixin(object):
    """
    Rest Framework resource mixin for resources that need to have concurrent
    accesses and editions controlled.
    """
    def _extract_param_version(self):
        param_version = self.request.DATA.get('version', None)
        try:
            param_version = param_version and int(param_version)
        except (ValueError, TypeError):
            raise exc.WrongArguments({"version": _("The version must be an integer")})

        return param_version

    def _validate_param_version(self, param_version, current_version):
        if param_version is None:
            return False
        else:
            if param_version < 0:
                return False
            if current_version is not None and param_version > current_version:
                return False

        return True

    def _validate_and_update_version(self, obj):
        current_version = None
        if obj.id:
            current_version = type(obj).objects.model.objects.get(id=obj.id).version

            # Extract param version
            param_version = self._extract_param_version()
            if not self._validate_param_version(param_version, current_version):
                raise exc.WrongArguments({"version": _("The version parameter is not valid")})

            if current_version != param_version:
                diff_versions = current_version - param_version

                modifying_fields = set(self.request.DATA.keys())
                if "version" in modifying_fields:
                    modifying_fields.remove("version")

                modified_fields = set(get_modified_fields(obj, diff_versions))
                if "version" in modifying_fields:
                    modified_fields.remove("version")

                both_modified = modifying_fields & modified_fields

                if both_modified:
                    raise exc.WrongArguments({"version": _("The version doesn't match with the current one")})

            obj.version = models.F('version') + 1

    def pre_save(self, obj):
        self._validate_and_update_version(obj)
        super().pre_save(obj)

    def post_save(self, obj, created=False):
        super().post_save(obj, created)
        if not created:
            obj.version = db.reload_attribute(obj, 'version')


class OCCModelMixin(models.Model):
    """
    Generic model mixin that makes model compatible
    with concurrency control system.
    """
    version = models.IntegerField(null=False, blank=False, default=1, verbose_name=_("version"))

    class Meta:
        abstract = True
