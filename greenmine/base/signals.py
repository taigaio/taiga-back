# -*- coding: utf-8 -*-

import django.dispatch

mail_new_user = django.dispatch.Signal(providing_args=["user"])
mail_recovery_password = django.dispatch.Signal(providing_args=["user"])

mail_question_created = django.dispatch.Signal(providing_args=["question", "user"])
mail_question_assigned = django.dispatch.Signal(providing_args=["question", "user"])
mail_question_deleted = django.dispatch.Signal(providing_args=["question", "user"])

mail_project_created = django.dispatch.Signal(providing_args=["project", "user"])
mail_project_modified = django.dispatch.Signal(providing_args=["project", "user"])
mail_project_deleted = django.dispatch.Signal(providing_args=["project", "user"])

mail_milestone_created = django.dispatch.Signal(providing_args=["milestone", "user"])
mail_milestone_modified = django.dispatch.Signal(providing_args=["milestone", "user"])
mail_milestone_deleted = django.dispatch.Signal(providing_args=["milestone", "user"])

mail_userstory_created = django.dispatch.Signal(providing_args=["us", "user"])
mail_userstory_modified = django.dispatch.Signal(providing_args=["us", "user"])
mail_userstory_deleted = django.dispatch.Signal(providing_args=["us", "user"])

mail_task_created = django.dispatch.Signal(providing_args=["task", "user"])
mail_task_modified = django.dispatch.Signal(providing_args=["task", "user"])
mail_task_assigned = django.dispatch.Signal(providing_args=["task", "user"])
mail_task_deleted = django.dispatch.Signal(providing_args=["task", "user"])
