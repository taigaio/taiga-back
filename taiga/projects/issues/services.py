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

import io
import csv

from taiga.base.utils import db, text

from . import models


def get_issues_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of issues.

    :param bulk_data: List of issues in bulk format.
    :param additional_fields: Additional fields when instantiating each issue.

    :return: List of `Issue` instances.
    """
    return [models.Issue(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_issues_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create issues from `bulk_data`.

    :param bulk_data: List of issues in bulk format.
    :param callback: Callback to execute after each issue save.
    :param additional_fields: Additional fields when instantiating each issue.

    :return: List of created `Issue` instances.
    """
    issues = get_issues_from_bulk(bulk_data, **additional_fields)
    db.save_in_bulk(issues, callback, precall)
    return issues


def update_issues_order_in_bulk(bulk_data):
    """Update the order of some issues.

    `bulk_data` should be a list of tuples with the following format:

    [(<issue id>, <new issue order value>), ...]
    """
    issue_ids = []
    new_order_values = []
    for issue_id, new_order_value in bulk_data:
        issue_ids.append(issue_id)
        new_order_values.append({"order": new_order_value})
    db.update_in_bulk_with_ids(issue_ids, new_order_values, model=models.Issue)


def issues_to_csv(queryset):
    csv_data = io.StringIO()
    fieldnames = ["ref", "subject", "description", "milestone", "owner",
                  "owner_full_name", "assigned_to", "assigned_to_full_name",
                  "status", "severity", "priority", "type", "is_closed",
                  "attachments", "external_reference"]
    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for issue in queryset:
        writer.writerow({
            "ref": issue.ref,
            "subject": issue.subject,
            "description": issue.description,
            "milestone": issue.milestone.name if issue.milestone else None,
            "owner": issue.owner.username,
            "owner_full_name": issue.owner.get_full_name(),
            "assigned_to": issue.assigned_to.username if issue.assigned_to else None,
            "assigned_to_full_name": issue.assigned_to.get_full_name() if issue.assigned_to else None,
            "status": issue.status.name,
            "severity": issue.severity.name,
            "priority": issue.priority.name,
            "type": issue.type.name,
            "is_closed": issue.is_closed,
            "attachments": issue.attachments.count(),
            "external_reference": issue.external_reference,
        })

    return csv_data
