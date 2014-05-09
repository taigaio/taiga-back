#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, lepture.com
# Copyright (c) 2014, taiga.io
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#    * Neither the name of the author nor the names of its contributors
#      may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re

from taiga.projects.userstories.models import UserStory
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task


def references(project, text):
    pattern = re.compile('(?<=^|(?<=[^a-zA-Z0-9-]))#(us|issue|task)(\d+)')

    def make_reference_link(m):
        obj_type = m.group(1)
        obj_ref = m.group(2)

        if obj_type == "us":
            model = UserStory
            obj_section = "user-story"
        elif obj_type == "issue":
            model = Issue
            obj_section = "issues"
        elif obj_type == "task":
            model = Task
            obj_section = "tasks"

        instances = model.objects.filter(project_id=project.id, ref=obj_ref)
        if not instances:
            return "#{type}{ref}".format(type=obj_type, ref=obj_ref)

        subject = instances[0].subject

        return '[#{type}{ref}](/#/project/{project_slug}/{section}/{ref} "{subject}")'.format(
            type=obj_type,
            section=obj_section,
            ref=obj_ref,
            project_slug=project.slug,
            subject=subject
        )

    text = pattern.sub(make_reference_link, text)
    return text

__all__ = ['references']
