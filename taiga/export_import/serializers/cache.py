# -*- coding: utf-8 -*-
from taiga.users import models as users_models

_cache_user_by_pk = {}
_cache_user_by_email = {}
_custom_tasks_attributes_cache = {}
_custom_issues_attributes_cache = {}
_custom_userstories_attributes_cache = {}
_custom_epics_attributes_cache = {}
_tasks_statuses_cache = {}
_issues_statuses_cache = {}
_userstories_statuses_cache = {}
_epics_statuses_cache = {}


def cached_get_user_by_pk(pk):
    if pk not in _cache_user_by_pk:
        try:
            _cache_user_by_pk[pk] = users_models.User.objects.get(pk=pk)
        except Exception:
            _cache_user_by_pk[pk] = users_models.User.objects.get(pk=pk)
    return _cache_user_by_pk[pk]


def cached_get_user_by_email(email):
    if email not in _cache_user_by_email:
        try:
            _cache_user_by_email[email] = users_models.User.objects.get(email=email)
        except Exception:
            _cache_user_by_email[email] = users_models.User.objects.get(email=email)
    return _cache_user_by_email[email]
