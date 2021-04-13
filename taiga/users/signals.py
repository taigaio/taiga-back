# -*- coding: utf-8 -*-
import django.dispatch


user_change_email = django.dispatch.Signal(providing_args=["user", "old_email", "new_email"])
user_cancel_account = django.dispatch.Signal(providing_args=["user", "request_data"])
