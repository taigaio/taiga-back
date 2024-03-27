# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import connection, migrations, models

def set_finished_date_for_tasks(apps, schema_editor):
    # Updates the finished date from tasks according to the history_entries associated
    # It takes the last history change updateing the status of a task and if it's a closed
    # one it updates the finished_date attribute
    sql="""
WITH status_update AS(
	WITH status_update AS(
		WITH history_entries AS (
			SELECT
				diff #>>'{status, 1}' new_status_id,
				regexp_split_to_array(key, ':') as split_key,
				created_at as date
			FROM history_historyentry
			WHERE diff #>>'{status, 1}' != ''
		)
		SELECT
			split_key[2] as object_id,
			new_status_id::int,
			MAX(date) as status_change_datetime
		FROM history_entries
		WHERE split_key[1] = 'tasks.task'
		GROUP BY object_id, new_status_id, date
	)
	SELECT status_update.*
	FROM status_update
	INNER JOIN projects_taskstatus
	ON projects_taskstatus.id = new_status_id AND projects_taskstatus.is_closed = True
)
UPDATE tasks_task
SET finished_date = status_update.status_change_datetime
FROM status_update
WHERE tasks_task.id = status_update.object_id::int
    """
    cursor = connection.cursor()
    cursor.execute(sql)

class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_remove_task_watchers'),
    ]

    operations = [
        migrations.RunPython(set_finished_date_for_tasks),
    ]
