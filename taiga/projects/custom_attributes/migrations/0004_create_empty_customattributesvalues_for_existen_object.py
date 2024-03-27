# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations


def create_empty_user_story_custom_attrributes_values(apps, schema_editor):
    cav_model = apps.get_model("custom_attributes", "UserStoryCustomAttributesValues")
    obj_model = apps.get_model("userstories", "UserStory")
    db_alias = schema_editor.connection.alias

    data = []
    for user_story in obj_model.objects.using(db_alias).all().select_related("custom_attributes_values"):
        if not hasattr(user_story, "custom_attributes_values"):
            data.append(cav_model(user_story=user_story,attributes_values={}))

    cav_model.objects.using(db_alias).bulk_create(data)


def delete_empty_user_story_custom_attrributes_values(apps, schema_editor):
    cav_model = apps.get_model("custom_attributes", "UserStoryCustomAttributesValues")
    db_alias = schema_editor.connection.alias

    cav_model.objects.using(db_alias).extra(where=["attributes_values::text <> '{}'::text"]).delete()


def create_empty_task_custom_attrributes_values(apps, schema_editor):
    cav_model = apps.get_model("custom_attributes", "TaskCustomAttributesValues")
    obj_model = apps.get_model("tasks", "Task")
    db_alias = schema_editor.connection.alias

    data = []
    for task in obj_model.objects.using(db_alias).all().select_related("custom_attributes_values"):
        if not hasattr(task, "custom_attributes_values"):
            data.append(cav_model(task=task,attributes_values={}))

    cav_model.objects.using(db_alias).bulk_create(data)


def delete_empty_task_custom_attrributes_values(apps, schema_editor):
    cav_model = apps.get_model("custom_attributes", "TaskCustomAttributesValues")
    db_alias = schema_editor.connection.alias

    cav_model.objects.using(db_alias).extra(where=["attributes_values::text <> '{}'::text"]).delete()


def create_empty_issues_custom_attrributes_values(apps, schema_editor):
    cav_model = apps.get_model("custom_attributes", "IssueCustomAttributesValues")
    obj_model = apps.get_model("issues", "Issue")
    db_alias = schema_editor.connection.alias

    data = []
    for issue in obj_model.objects.using(db_alias).all().select_related("custom_attributes_values"):
        if not hasattr(issue, "custom_attributes_values"):
            data.append(cav_model(issue=issue,attributes_values={}))

    cav_model.objects.using(db_alias).bulk_create(data)


def delete_empty_issue_custom_attrributes_values(apps, schema_editor):
    cav_model = apps.get_model("custom_attributes", "IssueCustomAttributesValues")
    db_alias = schema_editor.connection.alias

    cav_model.objects.using(db_alias).extra(where=["attributes_values::text <> '{}'::text"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0003_triggers_on_delete_customattribute'),
    ]

    operations = [
        migrations.RunPython(create_empty_user_story_custom_attrributes_values,
                             reverse_code=delete_empty_user_story_custom_attrributes_values,
                             atomic=True),
        migrations.RunPython(create_empty_task_custom_attrributes_values,
                             reverse_code=delete_empty_task_custom_attrributes_values,
                             atomic=True),
        migrations.RunPython(create_empty_issues_custom_attrributes_values,
                             reverse_code=delete_empty_issue_custom_attrributes_values,
                             atomic=True),
    ]
