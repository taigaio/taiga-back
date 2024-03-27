# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import response
from taiga.base.decorators import detail_route
from taiga.base.utils.collections import OrderedSet

from . import services
from . import validators


class TagsColorsResourceMixin:
    @detail_route(methods=["GET"])
    def tags_colors(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "tags_colors", project)

        return response.Ok(dict(project.tags_colors))

    @detail_route(methods=["POST"])
    def create_tag(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "create_tag", project)
        self._raise_if_blocked(project)

        validator = validators.CreateTagValidator(data=request.DATA, project=project)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        services.create_tag(project, data.get("tag"), data.get("color"))

        return response.Ok()

    @detail_route(methods=["POST"])
    def edit_tag(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "edit_tag", project)
        self._raise_if_blocked(project)

        validator = validators.EditTagTagValidator(data=request.DATA, project=project)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        services.edit_tag(project,
                          data.get("from_tag"),
                          to_tag=data.get("to_tag", None),
                          color=data.get("color", None))

        return response.Ok()

    @detail_route(methods=["POST"])
    def delete_tag(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "delete_tag", project)
        self._raise_if_blocked(project)

        validator = validators.DeleteTagValidator(data=request.DATA, project=project)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        services.delete_tag(project, data.get("tag"))

        return response.Ok()

    @detail_route(methods=["POST"])
    def mix_tags(self, request, pk=None):
        project = self.get_object()
        self.check_permissions(request, "mix_tags", project)
        self._raise_if_blocked(project)

        validator = validators.MixTagsValidator(data=request.DATA, project=project)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        services.mix_tags(project, data.get("from_tags"), data.get("to_tag"))

        return response.Ok()


class TaggedResourceMixin:
    def pre_save(self, obj):
        if obj.tags:
            self._pre_save_new_tags_in_project_tags_colors(obj)
        super().pre_save(obj)

    def _pre_save_new_tags_in_project_tags_colors(self, obj):
        new_obj_tags = OrderedSet()
        new_tags_colors = {}

        for tag in obj.tags:
            if isinstance(tag, (list, tuple)):
                name, color = tag
                name = name.lower()

                if color and not services.tag_exist_for_project_elements(obj.project, name):
                    new_tags_colors[name] = color

                new_obj_tags.add(name)
            elif isinstance(tag, str):
                new_obj_tags.add(tag.lower())

        obj.tags = list(new_obj_tags)

        if new_tags_colors:
            services.create_tags(obj.project, new_tags_colors)
