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

import json

from django import test
from django.core.urlresolvers import reverse
from django.core import mail
from django.db.models import get_model
from django.conf import settings

from taiga.users.tests import create_user
from taiga.projects.models import Project, Membership, ProjectTemplate
from taiga.domains.models import Domain

from . import create_project
from . import add_membership


class ProjectTemplateModelTestCase(test.TestCase):
    fixtures = ["initial_domains.json", "initial_project_templates.json"]

    def setUp(self):
        self.user = create_user(1)
        self.domain = Domain.objects.all()[0]
        self.template = ProjectTemplate.objects.get(slug="scrum")

    def test_apply_to_not_saved_project(self):
        not_saved_project = Project()
        self.assertRaises(Exception, self.template.apply_to_project, (not_saved_project,))

    def test_apply_to_saved_project(self):
        # Post-save apply the default template
        project = Project.objects.create(name="Test", slug="test", owner_id=1)
        self.assertEqual(project.creation_template.slug, settings.DEFAULT_PROJECT_TEMPLATE)

    def test_load_data_from_project_with_invalid_object(self):
        self.assertRaises(Exception, self.template.load_data_from_project, (None,))

    def test_load_data_from_project_not_defaults(self):
        project = Project.objects.create(name="Test", slug="test", owner_id=1)
        project.default_points = None
        project.default_us_status = None
        project.default_task_status = None
        project.default_issue_status = None
        project.default_issue_type = None
        project.default_priority = None
        project.default_severity = None

        template = ProjectTemplate()
        template.load_data_from_project(project)
        self.assertIsNone(template.default_options["points"])
        self.assertIsNone(template.default_options["us_status"])
        self.assertIsNone(template.default_options["task_status"])
        self.assertIsNone(template.default_options["issue_status"])
        self.assertIsNone(template.default_options["issue_type"])
        self.assertIsNone(template.default_options["priority"])
        self.assertIsNone(template.default_options["severity"])
