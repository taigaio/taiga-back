# -*- coding: utf-8 -*-
from __future__ import print_function
import sys

from rest_framework import views
from rest_framework import status, exceptions
from rest_framework.response import Response

def patch_api_view():
    from django.views.generic import View

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
            return super(APIView, self).handle_exception(exc)

        @classmethod
        def as_view(cls, **initkwargs):
            view = super(views._APIView, cls).as_view(**initkwargs)
            view.cls_instance = cls(**initkwargs)
            return view

    print("Patching APIView", file=sys.stderr)
    views.APIView = APIView
