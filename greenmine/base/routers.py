# -*- coding: utf-8 -*-

from rest_framework import routers


class DefaultRouter(routers.DefaultRouter):
    routes = [
        routers.Route(
            url=r'^{prefix}/(?P<pk>\d+)/restore/(?P<vpk>\d+)$',
            mapping={'post': 'restore'},
            name='{basename}-restore',
            initkwargs={}
        )
    ] + routers.DefaultRouter.routes

__all__ = ["DefaultRouter"]
