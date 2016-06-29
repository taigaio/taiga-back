# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, migrations, models
from django.utils.timezone import utc
import datetime


def update_totals(apps, schema_editor):
    model = apps.get_model("projects", "Project")
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql="""
        UPDATE projects_project
        SET
            totals_updated_datetime = totals.totals_updated_datetime,
            total_fans = totals.total_fans,
            total_fans_last_week = totals.total_fans_last_week,
            total_fans_last_month = totals.total_fans_last_month,
            total_fans_last_year = totals.total_fans_last_year,
            total_activity = totals.total_activity,
            total_activity_last_week = totals.total_activity_last_week,
            total_activity_last_month = totals.total_activity_last_month,
            total_activity_last_year = totals.total_activity_last_year
        FROM (
            WITH
            totals_activity AS (SELECT
            	split_part(timeline_timeline.namespace, ':', 2)::integer as project_id,
            	count(timeline_timeline.namespace) total_activity,
            	MAX (created) updated_datetime
            	FROM timeline_timeline
            	WHERE namespace LIKE 'project:%'
            	GROUP BY namespace),
            totals_activity_week AS (SELECT
            	split_part(timeline_timeline.namespace, ':', 2)::integer as project_id,
            	count(timeline_timeline.namespace) total_activity_last_week
            	FROM timeline_timeline
            	WHERE namespace LIKE 'project:%'
            	AND timeline_timeline.created > current_date - interval '7' day
            	GROUP BY namespace),
            totals_activity_month AS (SELECT
            	split_part(timeline_timeline.namespace, ':', 2)::integer as project_id,
            	count(timeline_timeline.namespace) total_activity_last_month
            	FROM timeline_timeline
            	WHERE namespace LIKE 'project:%'
            	AND timeline_timeline.created > current_date - interval '30' day
            	GROUP BY namespace),
            totals_activity_year AS (SELECT
            	split_part(timeline_timeline.namespace, ':', 2)::integer as project_id,
            	count(timeline_timeline.namespace) total_activity_last_year
            	FROM timeline_timeline
            	WHERE namespace LIKE 'project:%'
            	AND timeline_timeline.created > current_date - interval '365' day
            	GROUP BY namespace),
            totals_fans AS (SELECT
                object_id as project_id,
                COUNT(likes_like.object_id) total_fans,
                MAX (created_date) updated_datetime
                FROM likes_like
                WHERE content_type_id = {type_id}
                GROUP BY object_id),
            totals_fans_week AS (SELECT
                object_id as project_id,
                COUNT(likes_like.object_id) total_fans_last_week
                FROM likes_like
                WHERE content_type_id = {type_id}
                AND likes_like.created_date > current_date - interval '7' day
                GROUP BY object_id),
            totals_fans_month AS (SELECT
                object_id as project_id,
                COUNT(likes_like.object_id) total_fans_last_month
                FROM likes_like
                WHERE content_type_id = {type_id}
                AND likes_like.created_date > current_date - interval '30' day
                GROUP BY object_id),
            totals_fans_year AS (SELECT
                object_id as project_id,
                COUNT(likes_like.object_id) total_fans_last_year
                FROM likes_like
                WHERE content_type_id = {type_id}
                AND likes_like.created_date > current_date - interval '365' day
                GROUP BY object_id)
            SELECT
            	totals_activity.project_id,
            	COALESCE(total_activity, 0) total_activity,
            	COALESCE(total_activity_last_week, 0) total_activity_last_week,
            	COALESCE(total_activity_last_month, 0) total_activity_last_month,
            	COALESCE(total_activity_last_year, 0) total_activity_last_year,
            	COALESCE(total_fans, 0) total_fans,
            	COALESCE(total_fans_last_week, 0) total_fans_last_week,
            	COALESCE(total_fans_last_month, 0) total_fans_last_month,
            	COALESCE(total_fans_last_year, 0) total_fans_last_year,
            	totals_activity.updated_datetime totals_updated_datetime
            FROM totals_activity
            LEFT JOIN totals_fans ON totals_activity.project_id = totals_fans.project_id
            LEFT JOIN totals_fans_week ON totals_activity.project_id = totals_fans_week.project_id
            LEFT JOIN totals_fans_month ON totals_activity.project_id = totals_fans_month.project_id
            LEFT JOIN totals_fans_year ON totals_activity.project_id = totals_fans_year.project_id
            LEFT JOIN totals_activity_week ON totals_activity.project_id = totals_activity_week.project_id
            LEFT JOIN totals_activity_month ON totals_activity.project_id = totals_activity_month.project_id
            LEFT JOIN totals_activity_year ON totals_activity.project_id = totals_activity_year.project_id
        ) totals
        WHERE projects_project.id = totals.project_id
    """.format(type_id=type.id)

    cursor = connection.cursor()
    cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0029_project_is_looking_for_people'),
        ('timeline', '0004_auto_20150603_1312'),
        ('likes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='total_activity',
            field=models.PositiveIntegerField(default=0, verbose_name='count', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_activity_last_month',
            field=models.PositiveIntegerField(default=0, verbose_name='activity last month', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_activity_last_week',
            field=models.PositiveIntegerField(default=0, verbose_name='activity last week', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_activity_last_year',
            field=models.PositiveIntegerField(default=0, verbose_name='activity last year', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_fans',
            field=models.PositiveIntegerField(default=0, verbose_name='count', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_fans_last_month',
            field=models.PositiveIntegerField(default=0, verbose_name='fans last month', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_fans_last_week',
            field=models.PositiveIntegerField(default=0, verbose_name='fans last week', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_fans_last_year',
            field=models.PositiveIntegerField(default=0, verbose_name='fans last year', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='totals_updated_datetime',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 28, 7, 57, 11, 743976, tzinfo=utc), auto_now_add=True, verbose_name='updated date time', db_index=True),
            preserve_default=False,
        ),
        migrations.RunPython(update_totals),
    ]
