# -*- coding: utf-8 -*-
import django.dispatch


user_registered = django.dispatch.Signal(providing_args=["user"])
