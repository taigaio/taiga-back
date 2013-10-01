# -*- coding: utf-8 -*-

from rest_framework.response import Response
from rest_framework import views


class ApiRoot(views.APIView):
    def get(self, request, **kwargs):
        return Response({"name": "Greenmine Api",
                         "version": 1,
                         "info": "build with django-rest-framework"})
