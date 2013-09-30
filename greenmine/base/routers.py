# -*- coding: utf-8 -*-

from rest_framework import routers

# Special router for actions.
actions_router = routers.Route(url=r'^{prefix}/{methodname}{trailing_slash}$',
                               mapping={'{httpmethod}': '{methodname}'},
                               name='{basename}-{methodnamehyphen}',
                               initkwargs={})


class DefaultRouter(routers.DefaultRouter):
    routes = [
        routers.DefaultRouter.routes[0],
        actions_router,
        routers.DefaultRouter.routes[2],
        routers.DefaultRouter.routes[1]
    ]


class SimpleRouter(routers.SimpleRouter):
    routes = [
        routers.SimpleRouter.routes[0],
        actions_router,
        routers.SimpleRouter.routes[2],
        routers.SimpleRouter.routes[1]
    ]


__all__ = ["DefaultRouter", "SimpleRouter"]
