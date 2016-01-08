# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

# NOTE: This file is useful to translate default projects templates. Remember update
#       when taiga/projects/fixtures/initial_project_templates.json change.

from django.utils.translation import ugettext as _


##########################
## Default template information
##########################

# Translators: Name of scrum project template.
_("Scrum")
# Translators: Description of scrum project template.
_("The agile product backlog in Scrum is a prioritized features list, containing short descriptions of all functionality desired in the product. When applying Scrum, it's not necessary to start a project with a lengthy, upfront effort to document all requirements. The Scrum product backlog is then allowed to grow and change as more is learned about the product and its customers")

# Translators: Name of kanban project template.
_("Kanban")
# Translators: Description of kanban project template.
_("Kanban is a method for managing knowledge work with an emphasis on just-in-time delivery while not overloading the team members. In this approach, the process, from definition of a task to its delivery to the customer, is displayed for participants to see and team members pull work from a queue.")


##########################
## US Points
##########################

# Translators: User story point value (value = undefined)
_("?")
# Translators: User story point value (value = 0)
_("0")
# Translators: User story point value (value = 0.5)
_("1/2")
# Translators: User story point value (value = 1)
_("1")
# Translators: User story point value (value = 2)
_("2")
# Translators: User story point value (value = 3)
_("3")
# Translators: User story point value (value = 5)
_("5")
# Translators: User story point value (value = 8)
_("8")
# Translators: User story point value (value = 10)
_("10")
# Translators: User story point value (value = 13)
_("13")
# Translators: User story point value (value = 20)
_("20")
# Translators: User story point value (value = 40)
_("40")


##########################
## US Statuses
##########################

# Translators: User story status
_("New")

# Translators: User story status
_("Ready")

# Translators: User story status
_("In progress")

# Translators: User story status
_("Ready for test")

# Translators: User story status
_("Done")

# Translators: User story status
_("Archived")


##########################
## Task Statuses
##########################

# Translators: Task status
_("New")
# Translators: Task status
_("In progress")
# Translators: Task status
_("Ready for test")
# Translators: Task status
_("Closed")
# Translators: Task status
_("Needs Info")


##########################
## Issue Statuses
##########################

# Translators: Issue status
_("New")
# Translators: Issue status
_("In progress")
# Translators: Issue status
_("Ready for test")
# Translators: Issue status
_("Closed")
# Translators: Issue status
_("Needs Info")
# Translators: Issue status
_("Postponed")
# Translators: Issue status
_("Rejected")


##########################
## Issue Statuses
##########################

# Translators: Issue type
_("Bug")
# Translators: Issue type
_("Question")
# Translators: Issue type
_("Enhancement")


##########################
## Priorities
##########################

# Translators: Issue priority
_("Low")
# Translators: Issue priority
_("Normal")
# Translators: Issue priority
_("High")


##########################
## Severities
##########################
# Translators: Issue severity
_("Wishlist")
# Translators: Issue severity
_("Minor")
# Translators: Issue severity
_("Normal")
# Translators: Issue severity
_("Important")
# Translators: Issue severity
_("Critical")


##########################
## Roles
##########################
# Translators: User role
_("UX")
# Translators: User role
_("Design")
# Translators: User role
_("Front")
# Translators: User role
_("Back")
# Translators: User role
_("Product Owner")
# Translators: User role
_("Stakeholder")
