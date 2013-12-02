# -*- coding: utf-8 -*-
from __future__ import print_function
import sys


def patch_api_view():
    from rest_framework import views
    from rest_framework import status, exceptions
    from rest_framework.response import Response

    if hasattr(views, "_patched"):
        return

    views._APIView = views.APIView
    views._patched = True

    class APIView(views.APIView):
        def handle_exception(self, exc):
            if isinstance(exc, exceptions.NotAuthenticated):
                return Response({'detail': 'Not authenticated'},
                                status=status.HTTP_401_UNAUTHORIZED,
                                exception=True)
            return super().handle_exception(exc)

        @classmethod
        def as_view(cls, **initkwargs):
            view = super(views._APIView, cls).as_view(**initkwargs)
            view.cls_instance = cls(**initkwargs)
            view.cls = cls
            return view

    print("Patching APIView", file=sys.stderr)
    views.APIView = APIView


def patch_serializer():
    from rest_framework import serializers
    if hasattr(serializers.BaseSerializer, "_patched"):
        return

    def to_native(self, obj):
        """
        Serialize objects -> primitives.
        """
        ret = self._dict_class()
        ret.fields = self._dict_class()
        ret.empty = obj is None

        for field_name, field in self.fields.items():
            field.initialize(parent=self, field_name=field_name)
            key = self.get_field_key(field_name)
            ret.fields[key] = field

            if obj is not None:
                value = field.field_to_native(obj, field_name)
                ret[key] = value

        return ret

    serializers.BaseSerializer._patched = True
    serializers.BaseSerializer.to_native = to_native


def patch_import_module():
    from django.utils import importlib as django_importlib
    import importlib

    django_importlib.import_module = importlib.import_module


def patch_south_hacks():
    from south.hacks import django_1_0

    orig_set_installed_apps = django_1_0.Hacks.set_installed_apps
    def set_installed_apps(self, apps, preserve_models=True):
        return orig_set_installed_apps(self, apps, preserve_models=preserve_models)

    orig__redo_app_cache = django_1_0.Hacks._redo_app_cache
    def _redo_app_cache(self, preserve_models=True):
        return orig__redo_app_cache(self, preserve_models=preserve_models)

    django_1_0.Hacks.set_installed_apps = set_installed_apps
    django_1_0.Hacks._redo_app_cache = _redo_app_cache
